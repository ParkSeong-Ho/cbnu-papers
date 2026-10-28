# 디자인 가이드라인: Notion 제품 디자인 실측판

작성일: 2026-10-28 · 시안: `../mockup/notion-card-mockup.html` · 원본 측정값: `measured/*.json`

## 0. 이 문서의 근거

**Notion은 공식 디자인 시스템을 공개하지 않는다.** 검색되는 "Notion Design System" 자료는 전부 제3자가 역추출한 것이다. 게다가 대부분은 **notion.com 마케팅 사이트** 기준(파란 CTA `#0075de`, NotionInter 96px 히어로 등)이라, Notion 페이지 **안**에 들어갈 우리 결과물과는 맞지 않는다.

그래서 이 문서는 **공개된 notion.site 페이지 2곳을 브라우저로 열어 제품이 실제로 쓰는 값을 측정**해서 만들었다.

| 측정 대상 | 얻은 것 |
|---|---|
| `min-note-system.notion.site/…` | `:root, .notion-light-theme` CSS 변수 741개, 본문·제목·콜아웃 실측 |
| `binunu.notion.site/…` (Notion 공식 템플릿 갤러리 등록작) | select 태그(pill), 보드 카드, 제목 H1~H2, 다크 테마 값 |

- 측정일 2026-10-28, Playwright `getComputedStyle` 사용. 라이트·다크(`prefers-color-scheme`) 모두 측정했다.
- notion.site는 `prefers-color-scheme: dark`일 때 `.notion-dark-theme`로 바뀐다. **Notion 자체가 OS 테마를 따른다**는 뜻이므로, 우리 HTML도 같은 미디어 쿼리를 쓰면 함께 바뀔 가능성이 높다. 단, HTML 블록 iframe 안에서도 그런지는 업로드 테스트로 확인해야 한다.
- 이 값들은 Notion이 언제든 바꿀 수 있다. 변수 이름(`--c-texPri` 등)은 내부용이다.

### 이전 판(v1)에서 고친 것
| 항목 | v1 (커뮤니티 색표 기반) | **v2 (실측)** |
|---|---|---|
| 본문색 | `#37352f` | **`#2c2c2b`** |
| 태그 모양 | 사각 3px, 12px 글자 | **pill: 높이 20px, radius 10px, 14px 글자** |
| 태그 색 | 불투명 배경 `#e7f3f8` 등 | **반투명 배경 `{색}BacTerTra`** + 진한 글자 `{색}TexPri` |
| 카드 | 1px 테두리, 그림자 없음, radius 6px | **radius 10px, 1px 링 + 아주 옅은 그림자** |
| 다크 배경 | 추정값 | `#191919` / 카드 `#202020` 실측 |

---

## 1. 색

### 1.1 기본 (중립)
Notion 변수 이름을 그대로 쓴다. 나중에 실측 값과 대조하기 쉽게 하기 위해서다.

| 토큰 | 라이트 | 다크 | 용도 |
|---|---|---|---|
| `--c-texPri` | `#2c2c2b` | `#f0efed` | 본문, 제목 |
| `--c-texSec` | `#7d7a75` | `#ada9a3` | 보조 글자 (속성값, 저자, 날짜) |
| `--c-texTer` | `#a19e99` | `#7d7a75` | placeholder, 비활성 |
| `--c-bacPri` | `#ffffff` | `#191919` | 페이지 바탕 |
| `--c-bacSec` | `#f9f8f7` | `#202020` | 은은한 면 (코드 블록 계열) |
| `--c-bacEle` | `#ffffff` | `#202020` | 카드처럼 떠 있는 면 |
| `--ca-borPriTra` | `#1c13011c` | `#ffffeb1a` | 구분선, 콜아웃 테두리, 카드 링 |
| `--ca-butHovBac` | `#37352f0f` | `#ffffff0e` | hover 배경 |
| `--c-palUiBlu600` | `#2383e2` | `#2383e2` | 링크, 포커스, 선택 (Notion 파랑) |

### 1.2 태그 색 9종 (select / multi-select 실측)

**규칙: 글자 `--c-{색}TexPri` + 배경 `--ca-{색}BacTerTra`.** 라이트와 다크 모두 실측 태그와 정확히 일치했다.

| 색 | 라이트 글자 / 배경 | 다크 글자 / 배경 | 이 프로젝트 배정 (1차안) |
|---|---|---|---|
| gray | `#494846` / `#1c13011c` | `#f0efed` / `#fffceb4e` | 기타, 조사 중 |
| brown | `#584437` / `#7f330028` | `#f5ede9` / `#ffb8845d` | 시스템·OS |
| orange | `#6a4222` / `#c4580034` | `#fbebde` / `#ff8f477b` | 보안 |
| yellow | `#655121` / `#d19c0048` | `#f9f3dc` / `#ffbc3575` | 데이터·DB |
| green | `#2a533c` / `#00602628` | `#e8f1ec` / `#71ffaf56` | 네트워크·IoT |
| blue | `#264a72` / `#0076d934` | `#e5f2fc` / `#51a6ff7e` | 소프트웨어공학·테스트 |
| purple | `#553b69` / `#5c00a324` | `#f3ebf9` / `#d093ff6d` | AI·머신러닝 |
| pink | `#68354e` / `#b7004e27` | `#fae9f1` / `#ff85c06d` | HCI·그래픽스 |
| red | `#6d3531` / `#ce18002a` | `#fce9e7` / `#ff746986` | **🆕 신규 표시 전용** |

> 다크 모드 태그는 배경이 꽤 밝은 반투명이고 글자는 거의 흰색이다. 라이트와 생김새가 많이 다르니 다크도 반드시 확인한다.

### 1.3 강조 글자색 (태그 밖에서 색 글자가 필요할 때)
`--c-{색}TexSec`: blue `#387dc9`, red `#cf5148`, green `#50946e` 등. 다크에서도 값이 같다(실측). 예: "🆕 신규 2" 같은 짧은 강조 문구.

## 2. 타이포그래피

### 2.1 폰트 스택 (실측, 그대로 복사)
```css
font-family: ui-sans-serif, -apple-system, "system-ui", "Segoe UI Variable Display",
  "Segoe UI", Helvetica, "Apple Color Emoji", "Noto Sans Arabic", "Noto Sans Hebrew",
  Arial, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol";
```
한글은 macOS에서 Apple SD Gothic Neo, Windows에서 맑은 고딕으로 자연스럽게 떨어진다. Notion과 같은 경로라서 웹폰트를 쓰지 않아야 오히려 똑같이 보인다.

### 2.2 크기 (실측)
| 역할 | Notion 블록 | 크기 / 굵기 / 줄높이 |
|---|---|---|
| 페이지 제목 | page title | 40px / 700 / 48px |
| 제목 1 | `header` | 30px / 600 / 39px |
| 제목 2 | `sub_header` | 24px / 600 / 31.2px |
| 제목 3 | `sub_sub_header` | 20px / 600 / 26px |
| 본문 | `text` | 16px / 400 / 24px |
| DB 뷰 탭 | collection view tab | 14px / 500, padding 6px 12px |
| 태그 | select pill | 14px / 400, 높이 20px |
| 보조 | 속성값, 캡션 | 14px / 400, `--c-texSec` (실측 아님, Notion 관례) |

**HTML 블록 안에서는 제목 2(24px) 이하만 쓴다.** 블록이 놓이는 Notion 페이지에 이미 40px 페이지 제목이 있기 때문이다.

## 3. 형태

| 요소 | 실측 값 |
|---|---|
| 콘텐츠 폭 | 기본 폭 페이지에서 **664px** (전체 너비 모드는 더 넓음) |
| 콜아웃 | radius **10px**, padding 12px, `1px solid --ca-borPriTra`, 배경 투명 (기본 색 기준) |
| 보드/갤러리 카드 | radius **10px**, 배경 `--c-bacEle`, 너비 260px |
| 카드 그림자 (라이트) | `0 4px 12px #19191907, 0 1px 2px #19191905, 0 0 0 1px {링 색}` |
| 카드 그림자 (다크) | `0 2px 4px #19191914, 0 0 0 1px {링 색}` |
| 태그 pill | 높이 20px, radius **10px**, padding `0 9px 0 7px` |
| 인용 | 왼쪽 `3px solid` 본문색, padding-left 14px |
| 구분선 | 높이 1px, `--ca-borPriTra` |
| 포커스 링 | `#2383e291 0 0 0 1px inset, #2383e259 0 0 0 2px` (`--c-focSha`) |

> 링 색: 실측한 보드 카드는 그룹 색(green)으로 물든 링을 썼다. 우리 기본 카드는 중립 `--ca-borPriTra`를 쓴다.

간격은 Notion도 4px 배수 체계를 쓴다 (2·4·6·8·12·14·16·24). 마케팅 사이트 실측(4·8·12·16·24)과도 맞는다.

## 4. 컴포넌트

### 4.1 교수 카드 = Notion 갤러리 카드
```
╭────────────────────────────────╮  radius 10, 그림자 링
│ 🧪 홍신 연구실                   │  16px / 600
│ 소프트웨어학과                    │  14px texSec
│ ⦅퍼징 테스트⦆ ⦅뮤테이션 테스트⦆     │  blue pill
│ ⦅결함 위치 추정⦆                  │
│ 결함을 자동으로 찾고 원인을 좁힌다   │  14px texSec, 2줄 말줄임
│ 🆕 신규 2 · 논문 18편 · 2025       │  14px texSec, '신규'만 red TexSec
╰────────────────────────────────╯
```
- 너비는 `minmax(260px, 1fr)`. 실측 카드 너비 260px을 최소값으로 쓴다.
- hover하면 배경 `--ca-butHovBac`을 깐다. 그림자는 바꾸지 않는다.

### 4.2 연구주제 = select 태그
- 같은 카테고리는 모든 카드에서 같은 색.
- 카드 안에서는 태그를 먼저 보여주고, 설명은 카드 하단 한 줄로 몰아 쓴다. Notion 갤러리 카드에 속성이 나열되는 방식을 따른다.

### 4.3 논문 목록 = Notion 리스트 뷰
```
📄 Title of the paper …                 ⦅퍼징⦆   2025
   저자 · 학술지 · 피인용 3                          DOI ↗
```
- 행 사이에 선을 긋지 않는다. hover할 때만 배경 `--ca-butHovBac`, radius 6px.
- 신규 논문은 제목 앞에 red pill `🆕 신규`를 붙이고 목록 맨 위에 둔다.

### 4.4 상단 = 콜아웃 + 뷰 탭
- 콜아웃: `💡 마지막 업데이트 …`, radius 10, 1px 테두리, 배경 없음.
- 뷰 탭: `전체 · 소프트웨어 · 컴퓨터`. 14px / 500, padding 6px 12px.
  - 선택된 탭에 어떤 표시가 붙는지는 실측하지 못했다. 시안에서는 `--ca-butHovBac` 배경에 radius 6px로 표시했다. **업로드 후 실제 Notion 탭과 비교해 조정**한다.

## 5. HTML 블록 전용 규칙 (01 문서의 제약에서 나온 것)
1. 외부 요청 0개 (폰트, CDN, 이미지 모두). 아이콘은 이모지.
2. 최상위에 테두리와 배경을 칠하지 않는다. `body { background: transparent }`. Notion이 블록 테두리를 강제로 그리기 때문이다.
3. 라이트·다크 모두 `prefers-color-scheme`로 대응한다.
4. 제목은 24px 이하.

## 6. 쓰지 말 것
- notion.com 마케팅 사이트 값: 파란 버튼 `#0075de`, 보라 `#5645d4`, 96px 히어로, NotionInter 웹폰트. 제품 화면과 다르다.
- 불투명한 진한 배경색 블록, 그라데이션, 큰 그림자
- RnDcircle의 보라 배지

## 출처
- 실측: `min-note-system.notion.site`, `binunu.notion.site` (2026-10-28). 원본 JSON은 `docs/measured/`.
- 비교용 제3자 자료(마케팅 사이트 기준이거나 구버전 값): [oh-my-design.kr](https://oh-my-design.kr/design-systems/notion), [shadcn.io/design/notion](https://www.shadcn.io/design/notion), [designmd.co](https://www.designmd.co/d/notion), [Matthias Frank 색표](https://matthiasfrank.de/en/notion-colors/), [react-notion-x](https://github.com/NotionX/react-notion-x) (MIT)
