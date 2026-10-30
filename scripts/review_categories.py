"""M3 카테고리 초안 검토 페이지를 만든다.

docs/m3-categories.draft.json + data/papers.json → docs/m3-categories.html (외부 요청 없는 HTML 1개)
초안 JSON을 고친 뒤 다시 실행하면 태깅 결과가 갱신된다.

    python3 scripts/review_categories.py
"""
import json
from pathlib import Path

from fetch_papers import tag

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "docs" / "m3-categories.draft.json"
OUT = ROOT / "docs" / "m3-categories.html"
TOKENS = Path("/Users/se9078/my_hoop_things/notion-design-guide/tokens.css")


def build():
    draft = json.loads(DRAFT.read_text())
    profs = json.loads((ROOT / "data" / "professors.json").read_text())
    papers = json.loads((ROOT / "data" / "papers.json").read_text())
    rows = []
    for pr in sorted(profs, key=lambda p: p["order"]):
        d = draft.get(pr["id"], {"emoji": "📄", "summary": "", "categories": []})
        mine = [p for p in papers if pr["id"] in p["prof"]]
        rows.append({
            "id": pr["id"], "name": pr["name"], "dept": pr["dept"], "field": pr["field"],
            "emoji": d["emoji"], "summary": d["summary"], "categories": d["categories"],
            "papers": [{"t": p["title"], "y": p["year"], "v": p["venue"], "doi": p["doi"],
                        "c": p["cited"], "tags": tag(p, d)} for p in mine],
        })
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("/*TOKENS*/", TOKENS.read_text()).replace("/*DATA*/", data)
    OUT.write_text(html)
    print(OUT)


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>카테고리 초안 검토</title>
<style>
/*TOKENS*/
* { box-sizing: border-box; }
html { background: var(--c-bacPri); }
body { margin: 0; color: var(--c-texPri); font: 16px/24px var(--font); }
.wrap { max-width: 1080px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 30px; line-height: 39px; font-weight: 700; margin: 0 0 4px; }
h2 { font-size: 24px; line-height: 31px; font-weight: 600; margin: 0; }
h3 { font-size: 16px; line-height: 24px; font-weight: 600; margin: 24px 0 8px; }
.sec { color: var(--c-texSec); font-size: 14px; line-height: 20px; }
.ter { color: var(--c-texTer); }
button { font: inherit; color: inherit; }

.callout { display: flex; gap: 8px; margin: 16px 0; padding: 12px; border: 1px solid var(--ca-borPriTra); border-radius: var(--r-lg); background: var(--c-bacSec); }
.legend { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }

.bar { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; padding-bottom: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--ca-borPriTra); position: sticky; top: 0; background: var(--c-bacPri); z-index: 2; padding-top: 8px; }
.view { font: 500 14px/20px var(--font); color: var(--c-texSec); background: none; border: 0; border-radius: var(--r-sm); padding: 6px 12px; cursor: pointer; }
.view:hover { background: var(--ca-butHovBac); }
.view[aria-pressed="true"] { color: var(--c-texPri); background: var(--ca-butHovBac); }
.spacer { flex: 1; }
select, input[type=search] { font: 14px/20px var(--font); color: var(--c-texPri); background: none; border: 0; border-radius: var(--r-sm); padding: 6px 8px; cursor: pointer; }
input[type=search] { width: 180px; cursor: text; }
select:hover { background: var(--ca-butHovBac); }
:focus-visible { outline: 0; box-shadow: var(--sha-focus); }
input::placeholder { color: var(--c-texTer); }

.pill { display: inline-flex; align-items: center; height: 20px; padding: 0 9px 0 7px; border-radius: 10px; font-size: 14px; line-height: 20px; white-space: nowrap; }
.pills { display: flex; flex-wrap: wrap; gap: 4px 6px; }
.t-gray{color:var(--tag-gray-t);background:var(--tag-gray-b)} .t-brown{color:var(--tag-brown-t);background:var(--tag-brown-b)}
.t-orange{color:var(--tag-orange-t);background:var(--tag-orange-b)} .t-yellow{color:var(--tag-yellow-t);background:var(--tag-yellow-b)}
.t-green{color:var(--tag-green-t);background:var(--tag-green-b)} .t-blue{color:var(--tag-blue-t);background:var(--tag-blue-b)}
.t-purple{color:var(--tag-purple-t);background:var(--tag-purple-b)} .t-pink{color:var(--tag-pink-t);background:var(--tag-pink-b)}
.t-red{color:var(--tag-red-t);background:var(--tag-red-b)}

.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.card { text-align: left; background: var(--c-bacEle); border: 0; border-radius: var(--r-lg); box-shadow: var(--sha-card); padding: 14px; display: flex; flex-direction: column; gap: 8px; cursor: pointer; }
.card:hover { background-image: linear-gradient(var(--ca-butHovBac), var(--ca-butHovBac)); }
.card-title { font-weight: 600; display: flex; gap: 6px; }
.card .summary { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 40px; }
.foot { display: flex; align-items: center; gap: 8px; margin-top: auto; }
.meter { flex: 1; height: 4px; border-radius: 2px; background: var(--tag-gray-b); overflow: hidden; }
.meter i { display: block; height: 100%; background: var(--acc-green); }
.meter.low i { background: var(--acc-orange); }
.warn { color: var(--acc-orange); }

/* 상세: 오른쪽 패널. 좁은 화면에서는 전체 화면 */
.scrim { position: fixed; inset: 0; background: #0000002e; opacity: 0; pointer-events: none; transition: opacity .15s; z-index: 5; }
.panel { position: fixed; top: 0; right: 0; bottom: 0; width: min(720px, 100%); background: var(--c-bacPri); box-shadow: -1px 0 0 var(--ca-borPriTra), -8px 0 24px #0000001a; transform: translateX(100%); transition: transform .2s ease; z-index: 6; display: flex; flex-direction: column; }
.open .scrim { opacity: 1; pointer-events: auto; }
.open .panel { transform: none; }
.panel-head { display: flex; align-items: center; gap: 4px; padding: 8px 12px; border-bottom: 1px solid var(--ca-borPriTra); }
.icon-btn { background: none; border: 0; border-radius: var(--r-sm); padding: 4px 8px; cursor: pointer; color: var(--c-texSec); font-size: 14px; }
.icon-btn:hover { background: var(--ca-butHovBac); color: var(--c-texPri); }
.icon-btn:disabled { opacity: .35; cursor: default; background: none; }
.panel-body { overflow-y: auto; padding: 24px 24px 48px; }

.cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.cat { border-radius: var(--r-lg); box-shadow: var(--sha-card); padding: 12px; display: flex; flex-direction: column; gap: 6px; background: var(--c-bacEle); text-align: left; border: 0; cursor: pointer; }
.cat:hover { background-image: linear-gradient(var(--ca-butHovBac), var(--ca-butHovBac)); }
.cat[aria-pressed="true"] { box-shadow: var(--sha-focus); }
.cat .count { margin-left: auto; }
.kw { display: flex; flex-wrap: wrap; gap: 4px; }
.kw code { font: 12px/16px ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--c-texSec); background: var(--ca-butHovBac); border-radius: 4px; padding: 1px 5px; }
.kw.hide { display: none; }

.chips { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.list { list-style: none; margin: 0; padding: 0; }
.row { padding: 6px 8px; border-radius: var(--r-sm); display: flex; flex-direction: column; gap: 2px; }
.row:hover { background: var(--ca-butHovBac); }
.row .t { display: flex; flex-wrap: wrap; gap: 4px 6px; align-items: baseline; }
.row.untagged .t::before { content: "태그 없음"; font-size: 12px; line-height: 18px; padding: 0 6px; border-radius: 9px; color: var(--tag-orange-t); background: var(--tag-orange-b); }
a { color: inherit; text-decoration: underline; text-decoration-color: var(--c-texTer); text-underline-offset: 2px; }
.empty { padding: 24px 8px; text-align: center; }

.theme { position: fixed; right: 12px; bottom: 12px; font: 500 14px/20px var(--font); color: var(--c-texSec); background: var(--c-bacEle); border: 0; border-radius: var(--r-sm); padding: 6px 10px; box-shadow: var(--sha-card); cursor: pointer; z-index: 4; }

@media (max-width: 560px) {
  .spacer { display: none; }
  input[type=search] { width: 100%; }
  .panel-body { padding: 16px; }
}
</style>
</head>
<body>
<div class="wrap">
  <h1>🏷️ 연구주제 카테고리 초안</h1>
  <div class="sec" id="sub"></div>

  <div class="callout"><span>💡</span><div>
    <div>카드를 누르면 카테고리 설명과 실제로 태그가 붙은 논문을 볼 수 있습니다. <b>태깅률</b>이 낮을수록(주황) 카테고리가 논문을 잘 못 덮는다는 뜻입니다.</div>
    <div class="legend" id="legend"></div>
  </div></div>

  <div class="bar">
    <button class="view" data-dept="all" aria-pressed="true">🗂️ 전체</button>
    <button class="view" data-dept="software" aria-pressed="false">소프트웨어</button>
    <button class="view" data-dept="computer" aria-pressed="false">컴퓨터</button>
    <span class="spacer"></span>
    <select id="sort" aria-label="정렬">
      <option value="order">학과 순번</option>
      <option value="rate">태깅률 낮은 순</option>
      <option value="count">논문 많은 순</option>
    </select>
    <input type="search" id="q" placeholder="🔍 교수·카테고리 검색" aria-label="검색">
  </div>

  <div class="gallery" id="gallery"></div>
</div>

<div class="scrim" id="scrim"></div>
<aside class="panel" id="panel" role="dialog" aria-modal="true" aria-labelledby="ptitle">
  <div class="panel-head">
    <button class="icon-btn" id="close" aria-label="닫기">✕ 닫기</button>
    <span class="spacer"></span>
    <button class="icon-btn" id="prev" aria-label="이전 교수">↑ 이전</button>
    <button class="icon-btn" id="next" aria-label="다음 교수">↓ 다음</button>
  </div>
  <div class="panel-body" id="pbody"></div>
</aside>

<button class="theme" id="theme">🌓 테마</button>

<script>
const DATA = /*DATA*/;
const COLORS = { blue: "SW공학", purple: "AI·ML", orange: "보안", green: "네트워크·IoT", yellow: "데이터", brown: "시스템", pink: "그래픽스" };
const DEPT = { software: "소프트웨어학과", computer: "컴퓨터공학과" };
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pill = (c, text) => `<span class="pill t-${c}">${esc(text)}</span>`;

for (const p of DATA) {
  p.tagged = p.papers.filter(x => x.tags.length).length;
  p.rate = p.papers.length ? Math.round(100 * p.tagged / p.papers.length) : null;
}
const all = DATA.flatMap(p => p.papers), tagged = all.filter(x => x.tags.length).length;
$("#sub").textContent = `교수 ${DATA.length}명 · 논문 ${all.length}건 · 전체 태깅률 ${Math.round(100 * tagged / all.length)}%`;
$("#legend").innerHTML = Object.entries(COLORS).map(([c, t]) => pill(c, t)).join("");

const state = { dept: "all", sort: "order", q: "" };
let visible = [];

function matches(p, q) {
  if (!q) return true;
  const hay = [p.name, p.field, p.summary, ...p.categories.flatMap(c => [c.ko, c.en])].join(" ").toLowerCase();
  return hay.includes(q);
}

function renderGallery() {
  visible = DATA.filter(p => (state.dept === "all" || p.dept === state.dept) && matches(p, state.q));
  if (state.sort === "rate") visible.sort((a, b) => (a.rate ?? 101) - (b.rate ?? 101));
  if (state.sort === "count") visible.sort((a, b) => b.papers.length - a.papers.length);
  $("#gallery").innerHTML = visible.map(p => {
    const tags = p.categories.length ? p.categories.map(c => pill(c.color, c.ko)).join("") : pill("gray", "조사 중");
    const low = p.rate !== null && p.rate < 80;
    const foot = p.rate === null ? `<span class="sec">수집된 논문이 없습니다</span>`
      : `<span class="sec">논문 ${p.papers.length}편</span><span class="meter ${low ? "low" : ""}"><i style="width:${p.rate}%"></i></span><span class="sec ${low ? "warn" : ""}">${p.rate}%</span>`;
    return `<button class="card" data-id="${p.id}">
      <span class="card-title"><span>${p.emoji}</span><span>${esc(p.name)}</span></span>
      <span class="sec">${DEPT[p.dept]} · 홈페이지: ${esc(p.field)}</span>
      <span class="pills">${tags}</span>
      <span class="sec summary">${esc(p.summary)}</span>
      <span class="foot">${foot}</span>
    </button>`;
  }).join("") || `<div class="sec empty">검색 결과가 없습니다</div>`;
}

let cur = null, filter = "all", showKw = false;

function renderPanel() {
  const p = DATA.find(x => x.id === cur);
  if (!p) return;
  const idx = visible.findIndex(x => x.id === cur);
  $("#prev").disabled = idx <= 0;
  $("#next").disabled = idx < 0 || idx >= visible.length - 1;
  const count = k => p.papers.filter(x => x.tags.includes(k)).length;
  const untagged = p.papers.length - p.tagged;
  const byKey = Object.fromEntries(p.categories.map(c => [c.key, c]));
  const list = p.papers
    .filter(x => filter === "all" || (filter === "none" ? !x.tags.length : x.tags.includes(filter)))
    .sort((a, b) => b.y - a.y);

  $("#pbody").innerHTML = `
    <h2 id="ptitle">${p.emoji} ${esc(p.name)}</h2>
    <div class="sec">${DEPT[p.dept]} · 홈페이지 연구분야: ${esc(p.field)}</div>
    <p>${esc(p.summary) || '<span class="ter">요약 없음</span>'}</p>

    <h3>대표 연구 분야 <span class="sec">· 카드를 누르면 해당 논문만 봅니다</span></h3>
    ${p.categories.length ? `<div class="cats">${p.categories.map(c => `
      <button class="cat" data-filter="${c.key}" aria-pressed="${filter === c.key}">
        <span class="pills">${pill(c.color, c.ko)}<span class="sec count">${count(c.key)}편</span></span>
        <span class="sec">${esc(c.en)}</span>
        <span>${esc(c.desc)}</span>
        <span class="kw ${showKw ? "" : "hide"}">${c.match.map(m => `<code>${esc(m)}</code>`).join("")}</span>
      </button>`).join("")}</div>
      <p><button class="icon-btn" id="kw">${showKw ? "▾ 매칭 키워드 숨기기" : "▸ 매칭 키워드 보기"}</button></p>`
    : `<div class="sec">카테고리가 없습니다. ${pill("gray", "조사 중")}</div>`}

    <h3>논문 ${p.papers.length}편 <span class="sec">· 태깅률 ${p.rate ?? "—"}%</span></h3>
    <div class="chips">
      <button class="view" data-filter="all" aria-pressed="${filter === "all"}">전체 ${p.papers.length}</button>
      ${p.categories.map(c => `<button class="view" data-filter="${c.key}" aria-pressed="${filter === c.key}">${esc(c.ko)} ${count(c.key)}</button>`).join("")}
      ${untagged ? `<button class="view" data-filter="none" aria-pressed="${filter === "none"}">⚠️ 태그 없음 ${untagged}</button>` : ""}
    </div>
    <ul class="list">${list.map(x => `
      <li class="row ${x.tags.length ? "" : "untagged"}">
        <span class="t"><span>${esc(x.t)}</span>${x.tags.map(k => pill(byKey[k].color, byKey[k].ko)).join("")}</span>
        <span class="sec">${x.y} · ${esc(x.v) || "학술지 정보 없음"} · 피인용 ${x.c}${x.doi ? ` · <a href="https://doi.org/${esc(x.doi)}" target="_blank" rel="noopener">DOI↗</a>` : ""}</span>
      </li>`).join("") || `<li class="sec empty">해당하는 논문이 없습니다</li>`}
    </ul>`;
}

function open(id) {
  if (cur !== id) { filter = "all"; }
  cur = id;
  document.body.classList.add("open");
  renderPanel();
  $("#panel").querySelector(".panel-body").scrollTop = 0;
  if (location.hash !== "#p/" + id) history.replaceState(null, "", "#p/" + id);
  $("#close").focus();
}
function close() {
  const last = cur;
  cur = null;
  document.body.classList.remove("open");
  history.replaceState(null, "", location.pathname);
  document.querySelector(`.card[data-id="${last}"]`)?.focus();
}
function step(d) {
  const i = visible.findIndex(x => x.id === cur) + d;
  if (visible[i]) open(visible[i].id);
}

document.querySelectorAll(".bar .view").forEach(b => b.onclick = () => {
  state.dept = b.dataset.dept;
  document.querySelectorAll(".bar .view").forEach(x => x.setAttribute("aria-pressed", x === b));
  renderGallery();
});
$("#sort").onchange = e => { state.sort = e.target.value; renderGallery(); };
$("#q").oninput = e => { state.q = e.target.value.trim().toLowerCase(); renderGallery(); };
$("#gallery").onclick = e => { const c = e.target.closest(".card"); if (c) open(c.dataset.id); };
$("#pbody").onclick = e => {
  if (e.target.closest("a")) return;
  if (e.target.closest("#kw")) { showKw = !showKw; return renderPanel(); }
  const f = e.target.closest("[data-filter]");
  if (f) { filter = filter === f.dataset.filter && f.classList.contains("cat") ? "all" : f.dataset.filter; renderPanel(); }
};
$("#scrim").onclick = close;
$("#close").onclick = close;
$("#prev").onclick = () => step(-1);
$("#next").onclick = () => step(1);
document.addEventListener("keydown", e => {
  if (!cur) return;
  if (e.key === "Escape") close();
  if (e.target.matches("input, select")) return;
  if (e.key === "ArrowDown" || e.key === "j") { e.preventDefault(); step(1); }
  if (e.key === "ArrowUp" || e.key === "k") { e.preventDefault(); step(-1); }
});
$("#theme").onclick = () => {
  const r = document.documentElement, dark = r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  r.dataset.theme = dark ? "light" : "dark";
};

function route() {
  const m = location.hash.match(/^#p\/(.+)$/);
  if (m && DATA.some(p => p.id === m[1])) open(m[1]);
  else if (cur) close();
}
addEventListener("hashchange", route);
renderGallery();
route();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
