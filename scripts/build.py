"""화면을 만든다.

data/*.json + src/(template.html, app.js, tokens.css) → dist/index.html
데이터를 HTML 안에 넣어서 외부 요청이 하나도 없는 파일 1개를 만든다.
GitHub Pages와 Notion HTML 블록에 같은 파일을 쓸 수 있게 하기 위해서다.

- 카테고리 태그는 여기서 매번 tag() 로 계산한다 (papers.json 에 저장하지 않음).
- 신규 여부도 빌드 날짜 기준으로 다시 계산한다. 수집이 멈춰도 7일 지난 신규가 계속 뜨지 않게.

    python3 scripts/build.py
    python3 scripts/build.py --today 2026-11-09 --out /tmp/index.html
"""
import argparse
import copy
import datetime as dt
import json
from pathlib import Path

from fetch_papers import SINCE, clean, is_preprint, refresh_status, tag

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "src"
OUT = ROOT / "dist" / "index.html"


def payload(profs, papers, updates, today):
    papers = refresh_status(copy.deepcopy(papers), today)
    pmap = {p["id"]: p for p in profs}
    rows = []
    for w in papers:
        keys = []
        for pid in w["prof"]:
            for k in tag(w, pmap[pid]) if pid in pmap else []:
                if k not in keys:
                    keys.append(k)
        rows.append({
            "id": w["id"], "t": clean(w["title"]), "y": w["year"], "d": w.get("date") or "",
            "a": [clean(a) for a in w["authors"]], "v": clean(w["venue"]), "doi": w.get("doi") or "",
            "c": w.get("cited") or 0, "p": [pid for pid in w["prof"] if pid in pmap], "k": keys,
            "n": w["status"] == "new", "pre": is_preprint(w["venue"]),
        })
    rows.sort(key=lambda r: (r["d"], r["id"]), reverse=True)
    return {
        "updated": updates[-1]["today"] if updates else today,
        "y0": int(SINCE[:4]),
        "y1": max([int(today[:4])] + [r["y"] or 0 for r in rows]),
        "profs": [{
            "id": p["id"], "order": p["order"], "name": p["name"], "dept": p["dept"],
            "field": p.get("field", ""), "emoji": p.get("emoji") or "📄", "summary": p.get("summary", ""),
            "openalex": (p.get("openalex") or [""])[0],
            "cats": [{k: c[k] for k in ("key", "ko", "en", "color", "desc")} for c in p.get("categories", [])],
        } for p in sorted(profs, key=lambda p: p["order"])],
        "papers": rows,
    }


def build(today, out=OUT):
    profs = json.loads((DATA / "professors.json").read_text())
    papers = json.loads((DATA / "papers.json").read_text())
    updates = json.loads((DATA / "updates.json").read_text()) if (DATA / "updates.json").exists() else []
    data = json.dumps(payload(profs, papers, updates, today), ensure_ascii=False, separators=(",", ":"))
    html = ((SRC / "template.html").read_text()
            .replace("/*TOKENS*/", (SRC / "tokens.css").read_text())
            .replace("/*APP*/", (SRC / "app.js").read_text())
            .replace("/*DATA*/", data.replace("</", "<\\/")))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return html


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=dt.date.today().isoformat())
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    html = build(args.today, args.out)
    print(f"{args.out} ({len(html.encode()) // 1024}KB)")


if __name__ == "__main__":
    main()
