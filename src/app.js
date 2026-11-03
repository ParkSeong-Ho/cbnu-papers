// 화면 전환은 주소 뒤 #(해시)로만 한다: #/ 목록, #/p/{교수id} 상세. 필터·검색도 ?q= 로 해시에 넣어 뒤로 가기가 동작하게 한다.
// Notion HTML 블록(격리된 iframe)에서는 location 접근이 막힐 수 있어 모든 접근을 try/catch 로 감싸고, 실패하면 메모리 상태로 동작한다.
(() => {
  const D = JSON.parse(document.getElementById('data').textContent);
  const PROFS = D.profs;
  const byId = Object.fromEntries(PROFS.map(p => [p.id, p]));
  const CAT = {};
  PROFS.forEach(p => p.cats.forEach(c => { CAT[c.key] = c; }));
  const mine = Object.fromEntries(PROFS.map(p => [p.id, []]));
  D.papers.forEach(w => w.p.forEach(id => mine[id] && mine[id].push(w)));
  const DEPT = { software: '소프트웨어학과', computer: '컴퓨터공학과' };
  const YEARS = [];
  for (let y = D.y0; y <= D.y1; y++) YEARS.push(y);
  const THIS_YEAR = Number(D.updated.slice(0, 4));
  const NEW_TOTAL = D.papers.filter(w => w.n).length;
  const app = document.getElementById('app');

  const stat = id => {
    const ws = mine[id];
    return {
      n: ws.length,
      nw: ws.filter(w => w.n).length,
      last: ws.reduce((m, w) => Math.max(m, w.y || 0), 0),
      cited: ws.reduce((s, w) => s + (w.c || 0), 0),
    };
  };

  // ---------- 유틸 ----------
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = s => String(s ?? '').toLowerCase();
  const hl = (text, q) => {
    if (!q) return esc(text);
    const t = String(text ?? ''), lo = t.toLowerCase(), k = q.toLowerCase();
    let out = '', i = 0, j;
    while ((j = lo.indexOf(k, i)) !== -1) {
      out += esc(t.slice(i, j)) + '<mark>' + esc(t.slice(j, j + k.length)) + '</mark>';
      i = j + k.length;
    }
    return out + esc(t.slice(i));
  };
  const pill = (text, color) => `<span class="pill t-${color || 'gray'}">${esc(text)}</span>`;
  const authors = a => a.length > 3 ? `${a.slice(0, 3).join(', ')} 외 ${a.length - 3}명` : a.join(', ');
  const profUrl = id => '#/p/' + id;
  const sortProfs = list => list.slice().sort((a, b) => (stat(b.id).nw > 0) - (stat(a.id).nw > 0) || a.order - b.order);

  // ---------- 라우팅 ----------
  let mem = '#/';       // 해시를 못 쓰는 환경용
  let rendered = null;  // 마지막으로 그린 해시 (같은 해시로 hashchange 가 오면 다시 그리지 않음)
  let lastList = '#/';

  const parse = h => {
    h = (h || '').replace(/^#/, '') || '/';
    const [path, qs = ''] = h.split('?');
    const q = {};
    new URLSearchParams(qs).forEach((v, k) => { q[k] = v; });
    const m = path.match(/^\/p\/([\w-]+)/);
    return m ? { view: 'prof', id: m[1], q } : { view: 'list', q };
  };
  const fmt = st => {
    const qs = new URLSearchParams(Object.entries(st.q).filter(([, v]) => v)).toString();
    return '#' + (st.view === 'prof' ? '/p/' + st.id : '/') + (qs ? '?' + qs : '');
  };
  const readHash = () => { try { return location.hash; } catch (e) { return ''; } };

  // replace: 검색어 입력처럼 매 글자마다 뒤로 가기 기록이 쌓이면 안 되는 변경
  // draw=false: 화면은 호출한 쪽이 이미 부분 갱신함 (입력창 포커스 유지)
  function nav(st, { replace = false, draw = true } = {}) {
    const h = fmt(st);
    mem = h;
    rendered = h;
    try {
      if (readHash() !== h) replace ? location.replace(h) : (location.hash = h);
    } catch (e) { /* 격리된 iframe: 메모리 상태만 사용 */ }
    if (draw) render(st);
  }

  window.addEventListener('hashchange', () => {
    const h = readHash();
    if (h === rendered) return;
    rendered = h;
    mem = h;
    render(parse(h));
  });

  app.addEventListener('click', e => {
    const a = e.target.closest('a[href^="#/"]');
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    nav(parse(a.getAttribute('href')));
  });

  document.addEventListener('keydown', e => {
    if (e.key === '/' && !/^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName)) {
      const i = app.querySelector('input[type=search]');
      if (i) { e.preventDefault(); i.focus(); }
    }
  });

  let shownKey = null;  // 보던 화면 (목록 / 교수 id). 바뀔 때만 맨 위로 스크롤
  function render(st) {
    const ok = st.view === 'prof' && byId[st.id];
    if (ok) renderProf(st); else renderList(st.view === 'list' ? st : { view: 'list', q: {} });
    const key = ok ? st.id : 'list';
    if (shownKey !== null && key !== shownKey) { try { window.scrollTo(0, 0); } catch (e) {} }
    shownKey = key;
  }

  // ---------- 목록 #/ ----------
  const TABS = [
    { v: 'all', label: '전체', match: () => true },
    { v: 'software', label: '소프트웨어학과', match: p => p.dept === 'software' },
    { v: 'computer', label: '컴퓨터공학과', match: p => p.dept === 'computer' },
    { v: 'new', label: '🆕 신규', match: p => stat(p.id).nw > 0 },
  ];

  function renderList(st) {
    lastList = fmt(st);
    const v = TABS.some(t => t.v === st.q.v) ? st.q.v : 'all';
    const sw = PROFS.filter(p => p.dept === 'software').length;
    app.innerHTML = `
      <h1>📚 교수 논문 모아보기</h1>
      <div class="sec">충북대 소프트웨어학과 ${sw}명 · 컴퓨터공학과 ${PROFS.length - sw}명 · 최근 5년(${D.y0}~) 논문 ${D.papers.length}편</div>
      <div class="callout"><span>💡</span><span>마지막 업데이트 ${esc(D.updated)} · 이번 주 신규 ${
        NEW_TOTAL ? `<button class="linkbtn new" data-tab="new">${NEW_TOTAL}편</button>` : '0편'}</span></div>
      <div class="bar" role="tablist">
        ${TABS.map(t => `<button class="tab" role="tab" data-tab="${t.v}" aria-selected="${t.v === v}">${t.label}<span class="ct">${PROFS.filter(t.match).length}</span></button>`).join('')}
        <span class="spacer"></span>
        <label class="search"><span aria-hidden="true">🔍</span><input type="search" placeholder="이름·연구 분야·논문 제목" aria-label="검색" value="${esc(st.q.q || '')}"><button class="x" type="button" aria-label="검색어 지우기" hidden>✕</button></label>
      </div>
      <div id="res"></div>
      <p class="sec foot-note">출처: OpenAlex · 매주 월요일 자동 갱신 · 정부과제·특허 제외 · 연구 분야 태그는 제목·주제어로 자동 분류</p>`;

    const input = app.querySelector('input[type=search]');
    const x = app.querySelector('.x');
    const update = (draw) => {
      const q = input.value.trim();
      x.hidden = !q;
      fillList(v, q);
      if (draw !== false) nav({ view: 'list', q: { v: v === 'all' ? '' : v, q } }, { replace: true, draw: false });
      lastList = fmt({ view: 'list', q: { v: v === 'all' ? '' : v, q } });
    };
    input.addEventListener('input', () => update());
    x.addEventListener('click', () => { input.value = ''; update(); input.focus(); });
    app.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () =>
      nav({ view: 'list', q: { v: b.dataset.tab === 'all' ? '' : b.dataset.tab, q: input.value.trim() } })));
    update(false);
  }

  function profHits(p, q) {
    if (!q) return { self: true, papers: [] };
    const k = norm(q);
    const self = [p.name, p.field, p.summary, DEPT[p.dept], ...p.cats.flatMap(c => [c.ko, c.en])].some(s => norm(s).includes(k));
    const papers = mine[p.id].filter(w => norm(w.t).includes(k));
    return { self, papers };
  }

  function fillList(v, q) {
    const res = app.querySelector('#res');
    const tab = TABS.find(t => t.v === v);
    const shown = sortProfs(PROFS.filter(tab.match))
      .map(p => ({ p, h: profHits(p, q) }))
      .filter(({ h }) => h.self || h.papers.length);

    let html = '';
    if (v === 'new') html += newPapers(q);
    if (shown.length) {
      if (v === 'new') html += `<h3>신규 논문이 있는 교수</h3>`;
      html += `<div class="gallery">${shown.map(({ p, h }) => card(p, q, h)).join('')}</div>`;
    } else if (v !== 'new' || !NEW_TOTAL) {
      html += `<div class="empty sec">${q ? `‘${esc(q)}’와 일치하는 교수·논문이 없습니다.` : v === 'new' ? '이번 주 새로 발견된 논문이 없습니다.' : '교수 정보가 없습니다.'}</div>`;
    }
    res.innerHTML = html;
  }

  function card(p, q, h) {
    const s = stat(p.id);
    const tags = p.cats.length ? p.cats.map(c => pill(c.ko, c.color)).join('') : pill('조사 중', 'gray');
    const desc = s.n ? hl(p.summary, q) : '수집된 논문이 없습니다.';
    const foot = s.n
      ? [s.nw ? `<span class="new">🆕 신규 ${s.nw}</span>` : '', `논문 ${s.n}편`, `최근 ${s.last}`].filter(Boolean).join(' · ')
      : '논문 0편';
    const href = profUrl(p.id) + (q && h.papers.length ? '?q=' + encodeURIComponent(q) : '');
    return `<a class="card" href="${href}">
      <div class="card-title"><span>${esc(p.emoji)}</span><span>${hl(p.name, q)} 교수</span></div>
      <div class="sec">${esc(DEPT[p.dept])} · ${hl(p.field, q)}</div>
      <div class="pills">${tags}</div>
      <div class="sec desc">${desc}</div>
      <div class="sec foot">${foot}${q && h.papers.length ? ` · <span class="ter">🔎 논문 ${h.papers.length}편 일치</span>` : ''}</div>
    </a>`;
  }

  function newPapers(q) {
    const k = norm(q);
    const ws = D.papers.filter(w => w.n && (!k || norm(w.t).includes(k) || w.p.some(id => norm(byId[id].name).includes(k))));
    if (!ws.length) return q ? '' : `<div class="empty sec">이번 주 새로 발견된 논문이 없습니다.</div>`;
    return `<h3 style="margin-top:0">🆕 이번 주 새로 발견된 논문 ${ws.length}편</h3>
      <ul class="list">${ws.map(w => row(w, { q, showProf: true })).join('')}</ul>`;
  }

  // ---------- 논문 한 줄 ----------
  function row(w, { q = '', prof = null, showProf = false } = {}) {
    const keys = prof ? w.k.filter(k => prof.cats.some(c => c.key === k)) : w.k;
    const title = w.doi
      ? `<a href="https://doi.org/${esc(w.doi)}" target="_blank" rel="noopener">${hl(w.t, q)}</a>`
      : `<span class="tt">${hl(w.t, q)}</span>`;
    const others = w.p.filter(id => !prof || id !== prof.id);
    const who = others.length
      ? `${showProf ? '' : '함께: '}${others.map(id => `<a href="${profUrl(id)}">${esc(byId[id].name)}</a>`).join(', ')} · `
      : '';
    return `<li class="row${w.n && prof ? ' pinned' : ''}">
      <div class="t">${w.n ? pill('🆕 신규', 'red') : ''}${w.pre ? pill('프리프린트', 'gray') : ''}${title}</div>
      <div class="side">${keys.map(k => CAT[k] ? pill(CAT[k].ko, CAT[k].color) : '').join('')}</div>
      <div class="m sec">${w.y ? w.y + ' · ' : ''}${who}<span title="${esc(w.a.join(', '))}">${hl(authors(w.a), q)}</span>${w.v ? ` · ${hl(w.v, q)}` : ''} · 피인용 ${w.c}${w.doi ? ` · <a href="https://doi.org/${esc(w.doi)}" target="_blank" rel="noopener">DOI ↗</a>` : ''}</div>
    </li>`;
  }

  // ---------- 상세 #/p/{id} ----------
  function renderProf(st) {
    const p = byId[st.id];
    const s = stat(p.id);
    const f = { y: st.q.y || '', c: st.q.c || '', s: st.q.s === 'cited' ? 'cited' : '', q: st.q.q || '' };
    const set = (patch, opts) => nav({ view: 'prof', id: p.id, q: { ...f, ...patch } }, opts);
    const counts = {};
    mine[p.id].forEach(w => w.k.forEach(k => { counts[k] = (counts[k] || 0) + 1; }));
    const perYear = Object.fromEntries(YEARS.map(y => [y, mine[p.id].filter(w => w.y === y).length]));
    const max = Math.max(1, ...Object.values(perYear));
    const untagged = mine[p.id].filter(w => !w.k.some(k => p.cats.some(c => c.key === k))).length;

    app.innerHTML = `
      <a class="back" href="${esc(lastList)}">← 전체</a>
      <div class="ptitle"><span class="emo">${esc(p.emoji)}</span><h2>${esc(p.name)} 교수</h2></div>
      <div class="sec" style="margin-top:4px">${esc(DEPT[p.dept])} · ${esc(p.field)}${p.openalex ? ` · <a href="https://openalex.org/${esc(p.openalex)}" target="_blank" rel="noopener">OpenAlex ↗</a>` : ''}</div>
      ${s.n ? `<div class="stats sec"><span><b>${s.n}</b>편</span><span>피인용 <b>${s.cited}</b></span><span>최근 <b>${s.last}</b></span>${s.nw ? `<span class="new">🆕 신규 ${s.nw}편</span>` : ''}</div>
      <div class="callout" style="margin-bottom:0"><span>${esc(p.emoji)}</span><span>${esc(p.summary)}</span></div>` : ''}

      <h3>대표 연구 분야</h3>
      ${p.cats.length ? `<div class="cats">${p.cats.map(c => `
        <button class="cat" data-cat="${esc(c.key)}" aria-pressed="${f.c === c.key}">
          <span>${pill(c.ko, c.color)}</span>
          <span class="sec en">${esc(c.en)}</span>
          <span class="sec">${esc(c.desc)}</span>
          <span class="sec ct">논문 ${counts[c.key] || 0}편 →</span>
        </button>`).join('')}</div>` : `<div class="pills">${pill('조사 중', 'gray')}</div><p class="sec">수집된 논문이 없어 연구 분야를 아직 정하지 않았습니다.</p>`}

      ${s.n ? `
      <h3>연구 성과 추이</h3>
      <div class="chart" role="group" aria-label="연도별 논문 수">${YEARS.map(y => `
        <button class="col${y === THIS_YEAR ? ' cur' : ''}" data-year="${y}" aria-pressed="${f.y === String(y)}" title="${y}년 ${perYear[y]}편${y === THIS_YEAR ? ' (올해, 진행 중)' : ''}">
          <span class="v">${perYear[y]}</span><span class="b" style="height:${Math.round(perYear[y] / max * 110)}px"></span>
        </button>`).join('')}</div>
      <div class="years">${YEARS.map(y => `<span>${y === THIS_YEAR ? y + '*' : y}</span>`).join('')}</div>
      <div class="sec ter" style="margin-top:4px">* 올해는 진행 중 · 막대를 누르면 그 해 논문만 봅니다</div>

      <h3>논문 목록</h3>
      <div class="tools">
        <select data-f="y" aria-label="연도"><option value="">전체 연도</option>${YEARS.slice().reverse().map(y => `<option value="${y}"${f.y === String(y) ? ' selected' : ''}>${y}년 (${perYear[y]})</option>`).join('')}</select>
        <select data-f="c" aria-label="연구 분야"><option value="">전체 분야</option>${p.cats.map(c => `<option value="${esc(c.key)}"${f.c === c.key ? ' selected' : ''}>${esc(c.ko)} (${counts[c.key] || 0})</option>`).join('')}${untagged ? `<option value="none"${f.c === 'none' ? ' selected' : ''}>분류 안 됨 (${untagged})</option>` : ''}</select>
        <select data-f="s" aria-label="정렬"><option value="">최신순</option><option value="cited"${f.s ? ' selected' : ''}>피인용순</option></select>
        <label class="search"><span aria-hidden="true">🔍</span><input type="search" placeholder="제목·저자·학술지" aria-label="논문 검색" value="${esc(f.q)}"><button class="x" type="button" aria-label="검색어 지우기" hidden>✕</button></label>
        <span class="sec count" id="count"></span>
      </div>
      <ul class="list" id="rows"></ul>` : `<div class="empty sec">수집된 논문이 없습니다.</div>`}`;

    if (!s.n) return;
    app.querySelectorAll('[data-cat]').forEach(b => b.addEventListener('click', () => set({ c: f.c === b.dataset.cat ? '' : b.dataset.cat })));
    app.querySelectorAll('[data-year]').forEach(b => b.addEventListener('click', () => set({ y: f.y === b.dataset.year ? '' : b.dataset.year })));
    app.querySelectorAll('select[data-f]').forEach(sel => sel.addEventListener('change', () => set({ [sel.dataset.f]: sel.value })));
    const input = app.querySelector('input[type=search]');
    const x = app.querySelector('.x');
    const update = (write) => {
      f.q = input.value.trim();
      x.hidden = !f.q;
      fillRows(p, f, set);
      if (write !== false) set({ q: f.q }, { replace: true, draw: false });
    };
    input.addEventListener('input', () => update());
    x.addEventListener('click', () => { input.value = ''; update(); input.focus(); });
    update(false);
  }

  function fillRows(p, f, set) {
    const k = norm(f.q);
    let ws = mine[p.id].filter(w =>
      (!f.y || String(w.y) === f.y) &&
      (!f.c || (f.c === 'none' ? !w.k.some(x => p.cats.some(c => c.key === x)) : w.k.includes(f.c))) &&
      (!k || [w.t, w.v, ...w.a].some(s => norm(s).includes(k))));
    ws = ws.slice().sort((a, b) => (b.n - a.n) || (f.s === 'cited' ? b.c - a.c : 0) || (b.d > a.d ? 1 : b.d < a.d ? -1 : 0));
    const total = mine[p.id].length;
    const filtered = f.y || f.c || f.q;
    app.querySelector('#count').innerHTML = filtered ? `${ws.length}편 / 전체 ${total}편 · <button class="linkbtn" id="reset">필터 초기화</button>` : `${total}편`;
    app.querySelector('#rows').innerHTML = ws.length
      ? ws.map(w => row(w, { q: f.q, prof: p })).join('')
      : `<li class="empty sec">조건에 맞는 논문이 없습니다.</li>`;
    const r = app.querySelector('#reset');
    if (r) r.addEventListener('click', () => set({ y: '', c: '', q: '' }));
  }

  // ---------- 시작 ----------
  const start = readHash() || mem;
  rendered = start;
  render(parse(start));
})();
