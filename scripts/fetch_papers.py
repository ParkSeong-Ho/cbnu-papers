"""OpenAlex에서 교수별 논문을 받아 data/papers.json 을 갱신한다.

매 실행마다 수집 기간 전체를 다시 받아 피인용 수를 최신으로 맞추고,
처음 보는 논문만 added_at=오늘, status=new 로 넣는다.
처음 수집되는 교수(기존 papers.json 에 논문이 하나도 없는 교수)의 논문은 전부 normal 로 넣는다.
그래야 첫 실행이나 교수를 새로 추가한 주에 수백 편이 한꺼번에 "신규"로 뜨지 않는다.
이번에 수집에 성공한 교수의 결과에서 빠진 논문은 그 교수와의 연결을 끊는다 (제외 규칙 변경 등).
카테고리 태그는 저장하지 않는다. 카테고리는 자주 다듬으므로 build.py 가 매번 tag() 로 계산한다.

    python3 scripts/fetch_papers.py            # 평소 실행
    python3 scripts/fetch_papers.py --today 2026-11-02   # 날짜 고정 (테스트·재현용)
"""
import argparse
import datetime as dt
import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
API = "https://api.openalex.org/works"
CBNU = "I163753206"
CS_FIELD = "fields/17"
SINCE = "2021-01-01"
NEW_DAYS = 7
DROP_GUARD = 0.5   # 한 교수의 수집 결과가 기존의 절반 미만이면 API 이상으로 보고 이번 결과를 버린다
FUZZY = 0.9        # 프리프린트-정식본 제목 유사도 기준
KEEP_RUNS = 52
SELECT = ",".join([
    "id", "doi", "title", "publication_year", "publication_date", "type",
    "authorships", "primary_location", "cited_by_count", "primary_topic", "keywords",
])
SKIP_TYPES = {"erratum", "paratext", "retraction", "peer-review"}
SKIP_TITLE = re.compile(r"^\s*(correction|erratum|corrigendum|retraction)\b", re.I)
PREPRINT_VENUES = ("arxiv", "ssrn", "biorxiv", "medrxiv", "research square", "techrxiv", "preprints")


# ---------- 순수 함수 (테스트 대상) ----------

def norm_title(title):
    t = unicodedata.normalize("NFKC", title or "").lower()
    return re.sub(r"[^0-9a-z가-힣]+", "", t)


def short_id(url):
    return (url or "").rsplit("/", 1)[-1]


def is_preprint(venue):
    v = (venue or "").lower()
    return any(p in v for p in PREPRINT_VENUES)


def keep_work(work, prof):
    """교수 설정(소속·분야 필터)과 제외 규칙에 맞는 논문인지."""
    if work.get("type") in SKIP_TYPES or SKIP_TITLE.match(work.get("title") or ""):
        return False
    if not work.get("title"):
        return False
    field = (((work.get("primary_topic") or {}).get("field")) or {}).get("id", "")
    ex = prof.get("exclude") or {}
    if any(field.endswith(f) for f in ex.get("fields", [])):
        return False
    text = " ".join([work["title"]] + [k.get("display_name", "") for k in work.get("keywords") or []]).lower()
    if any(m.lower() in text for m in ex.get("match", [])):
        return False
    ids = set(prof["openalex"])
    if prof.get("affiliation_filter"):
        mine = [a for a in work.get("authorships", []) if short_id((a.get("author") or {}).get("id")) in ids]
        if not any(short_id(i.get("id")) == CBNU for a in mine for i in a.get("institutions", [])):
            return False
    if prof.get("field_filter"):
        if not field.endswith(CS_FIELD):
            return False
    return True


def to_paper(work):
    loc = work.get("primary_location") or {}
    venue = (loc.get("source") or {}).get("display_name") or ""
    doi = (work.get("doi") or "").replace("https://doi.org/", "").lower()
    topics = [(work.get("primary_topic") or {}).get("display_name") or ""]
    keywords = [k.get("display_name", "") for k in work.get("keywords") or []]
    return {
        "id": short_id(work["id"]),
        "title": work["title"].strip(),
        "year": work.get("publication_year"),
        "date": work.get("publication_date"),
        "authors": [(a.get("author") or {}).get("display_name", "") for a in work.get("authorships", [])],
        "venue": venue,
        "doi": doi,
        "cited": work.get("cited_by_count", 0),
        "terms": [t for t in topics + keywords if t],
        "source": "openalex",
    }


def term_re(m):
    """match 키워드 → 정규식. 단어 단위로 찾는다 (edge 가 knowledge 에 걸리지 않게).
    끝에 * 를 붙이면 그 글자로 시작하는 단어 전부: "fuzz*" → fuzz, fuzzing, fuzzed. 아니면 복수형(s, es)까지."""
    m = m.lower().strip()
    if m.endswith("*"):
        return re.compile(r"\b" + re.escape(m[:-1]))
    return re.compile(r"\b" + re.escape(m) + r"(?:s|es)?\b")


def tag(paper, prof):
    """교수 카테고리의 match 키워드가 제목·주제어에 걸리면 그 카테고리 key 목록. (build.py 에서 사용)"""
    text = " ".join([paper["title"]] + paper.get("terms", [])).lower()
    return [c["key"] for c in prof.get("categories", [])
            if any(term_re(m).search(text) for m in c.get("match", []))]


def better(a, b):
    """같은 논문의 두 판본 중 보여줄 것. 정식 출판본 > 프리프린트, 그다음 피인용 수."""
    ka = (not is_preprint(a["venue"]), a["cited"])
    kb = (not is_preprint(b["venue"]), b["cited"])
    return a if ka >= kb else b


def merge(existing, fetched, today, baseline):
    """기존 목록과 이번 수집분을 합친다.

    existing: 기존 papers 목록
    fetched:  {prof_id: [paper, ...]}  수집에 성공한 교수만 들어 있다
    같은 논문 판정: DOI → OpenAlex ID → (정규화 제목 + 연도)
                   → 한쪽이 프리프린트면 연도 ±2년, 제목 유사도 FUZZY 이상
    처음 보는 논문만 added_at=today, status=new. 단 baseline(교수 id 집합)에 든 교수의 논문은 normal.
    fetched 에 있는 교수인데 이번 결과에 없는 논문은 그 교수를 prof 에서 뺀다. prof 가 비면 논문을 지운다.
    레코드의 id 는 처음 본 판본의 OpenAlex ID 로 고정한다 (외부에서 이 id 로 연결하므로).
    """
    by_key = {}
    buckets = {}
    out = []

    def keys(p):
        ks = [("id", p["id"]), ("t", norm_title(p["title"]), p["year"])]
        if p.get("doi"):
            ks.append(("doi", p["doi"]))
        return ks

    def find(p):
        for k in keys(p):
            if k in by_key:
                return by_key[k]
        t = norm_title(p["title"])
        for c in buckets.get(t[:20], []):
            if (is_preprint(p["venue"]) or is_preprint(c["venue"])) and abs((p["year"] or 0) - (c["year"] or 0)) <= 2 \
                    and difflib.SequenceMatcher(None, t, norm_title(c["title"])).ratio() >= FUZZY:
                return c
        return None

    def index(p):
        for k in keys(p):
            by_key[k] = p
        b = buckets.setdefault(norm_title(p["title"])[:20], [])
        if p not in b:
            b.append(p)

    def fold(old, new):
        if better(old, new) is new:
            for f in ("title", "year", "date", "authors", "venue", "doi", "terms", "source"):
                if new.get(f):
                    old[f] = new[f]
        old["cited"] = max(old.get("cited", 0), new.get("cited", 0))
        index(old)

    for p in existing:
        p = dict(p, prof=list(p["prof"]))
        old = find(p)
        if old is None:
            out.append(p)
            index(p)
            continue
        # 기존 목록 안의 중복 (판정 규칙이 바뀐 경우): 먼저 발견한 쪽의 날짜·상태를 남긴다
        if p["added_at"] < old["added_at"]:
            old["added_at"], old["status"], old["id"] = p["added_at"], p["status"], p["id"]
        old["prof"] += [q for q in p["prof"] if q not in old["prof"]]
        fold(old, p)

    matched = {pid: set() for pid in fetched}
    for prof_id, papers in fetched.items():
        for new in papers:
            old = find(new)
            if old is None:
                rec = dict(new)
                rec["prof"] = [prof_id]
                rec["added_at"] = today
                rec["status"] = "normal" if prof_id in baseline else "new"
                out.append(rec)
                index(rec)
                matched[prof_id].add(id(rec))
                continue
            fold(old, new)
            if prof_id not in old["prof"]:
                old["prof"].append(prof_id)
            matched[prof_id].add(id(old))
    for p in out:
        p["prof"] = [q for q in p["prof"] if q not in matched or id(p) in matched[q]]
    return [p for p in out if p["prof"]]


def refresh_status(papers, today):
    """added_at 이 NEW_DAYS 일 넘게 지난 new 를 normal 로 바꾼다."""
    t = dt.date.fromisoformat(today)
    for p in papers:
        if p.get("status") == "new" and (t - dt.date.fromisoformat(p["added_at"])).days >= NEW_DAYS:
            p["status"] = "normal"
    return papers


# ---------- 네트워크 ----------

def get_json(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cbnu-papers (github.com/ParkSeong-Ho/cbnu-papers)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or i == tries - 1:
                raise
        except urllib.error.URLError:
            if i == tries - 1:
                raise
        time.sleep(2 ** i)


def fetch_works(author_ids, since, cs_only=False):
    # 분야 필터는 서버에서 건다. 입자물리 대형 공동연구처럼 저자가 수천 명인 논문이
    # 섞인 프로필은 그대로 받으면 응답이 수 MB 로 커져 잘린다.
    flt = f"authorships.author.id:{'|'.join(author_ids)},from_publication_date:{since}"
    if cs_only:
        flt += f",primary_topic.field.id:{CS_FIELD}"
    cursor = "*"
    works = []
    while cursor:
        q = urllib.parse.urlencode({
            "filter": flt,
            "select": SELECT, "per_page": 200, "cursor": cursor,
        })
        d = get_json(f"{API}?{q}")
        works += d["results"]
        cursor = d["meta"].get("next_cursor") if d["results"] else None
        time.sleep(0.1)
    return works


# ---------- 실행 ----------

def load(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=dt.date.today().isoformat())
    args = ap.parse_args(argv)

    profs = json.loads((DATA / "professors.json").read_text())
    existing = load("papers.json", [])
    seen = {pid for p in existing for pid in p["prof"]}
    updates = load("updates.json", [])

    fetched, errors = {}, []
    for prof in profs:
        if not prof["openalex"]:
            continue
        try:
            works = fetch_works(prof["openalex"], SINCE, prof.get("field_filter", False))
        except Exception as e:  # 한 교수가 실패해도 나머지는 계속
            errors.append({"prof": prof["id"], "error": f"{type(e).__name__}: {e}"})
            continue
        papers = [to_paper(w) for w in works if keep_work(w, prof)]
        had = sum(prof["id"] in p["prof"] for p in existing)
        if had >= 5 and len(papers) < had * DROP_GUARD:
            errors.append({"prof": prof["id"], "error": f"수집 결과 급감 {had}→{len(papers)}편, 이번 결과 무시"})
            continue
        fetched[prof["id"]] = papers
        print(f"{prof['id']:<18} {len(works):>4} 받음 → {len(papers):>4} 채택", file=sys.stderr)

    baseline = {pid for pid in fetched if pid not in seen}
    before = {p["id"] for p in existing}
    papers = refresh_status(merge(existing, fetched, args.today, baseline), args.today)
    papers.sort(key=lambda p: (p.get("date") or "", p["id"]), reverse=True)
    added = [p for p in papers if p["id"] not in before and p["status"] == "new"]
    removed = len(before - {p["id"] for p in papers})

    by_prof = {}
    for p in added:
        for pid in p["prof"]:
            by_prof[pid] = by_prof.get(pid, 0) + 1
    updates.append({
        "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "today": args.today, "baseline": sorted(baseline), "total": len(papers),
        "new": len(added), "removed": removed, "by_prof": by_prof, "errors": errors,
    })
    save("papers.json", papers)
    save("updates.json", updates[-KEEP_RUNS:])
    print(f"총 {len(papers)}편, 신규 {len(added)}편, 삭제 {removed}편, 첫 수집 교수 {len(baseline)}명, 오류 {len(errors)}건", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
