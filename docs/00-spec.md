# 개발 명세 v2: 충북대 SW·컴공 교수 논문 모아보기

작성일: 2026-10-28 · 디자인: `/Users/se9078/my_hoop_things/notion-design-guide/` · 시안: `mockup/notion-card-mockup.html`

## 1. 확정 사항

| 항목 | 결정 |
|---|---|
| 대상 | 18명: 소프트웨어학과 12(홍신, 이의종, 조희승, 조오현, 나스리디노프 아지즈, 이종연, 류관희, 최경주, 홍장의, 이건명, 노서영, 강윤석) + 컴퓨터공학과 6(조겨리, 김봉재, 정영섭, 김진우, 박수창, 김성진) |
| 초기 수집 | 최근 5년 (2021-01-01 ~) |
| 갱신 | 1주일에 한 번 자동 (GitHub Actions) |
| 제외 | 정부과제, 특허 |
| 저장소 | GitHub 저장소 + GitHub Actions + GitHub Pages |
| 노출 | 1단계: GitHub Pages를 Notion에 embed → 2단계: Notion HTML 블록 (테스트 통과 시) |
| 디자인 | Notion 실측 가이드 (`notion-design-guide/`) |

## 2. 화면

**결과물은 HTML 파일 1개다.** 데이터를 HTML 안에 넣고 외부 요청을 하나도 쓰지 않는다. 그래야 GitHub Pages와 Notion HTML 블록 양쪽에 같은 파일을 쓸 수 있다. 화면 전환은 주소 뒤 `#`(해시)로 한다.

### 2.1 목록 `#/`  (시안 그대로)
- 콜아웃: `💡 마지막 업데이트 YYYY-MM-DD · 이번 주 신규 N편`
- 뷰 탭: `전체 · 소프트웨어 · 컴퓨터 · 🆕 신규`, 오른쪽에 검색창 (이름·연구실·카테고리·논문 제목 검색)
- 갤러리 카드 18장. 카드 하나에 들어가는 것:
  - 이모지, 연구실 이름, 학과·교수 이름
  - 연구주제 태그 최대 3개, 설명 2줄
  - `🆕 신규 N` (0이면 숨김), 논문 수, 최근 연도
- 정렬: 신규가 있는 카드 → 나머지는 원래 순번(스크린샷의 1~15)

### 2.2 교수 상세 `#/p/{id}`
- `← 전체` 링크, 제목(24px), 학과
- **대표 연구 분야**: 카테고리 카드 3장 (태그 + 한글명/영문명 + 설명 2~3줄)
- **연구 성과 추이**: 2021~올해 연도별 논문 수 막대 (인라인 SVG, 라이브러리 없음)
- **논문 목록** (리스트 뷰)
  - 필터: 연도, 카테고리 / 정렬: 최신순(기본), 피인용순
  - 행: 신규 pill, 제목, 카테고리 태그, 연도 / 저자 · 학술지 · 피인용 · DOI↗
  - 신규 논문은 맨 위에 고정

### 2.3 공통
- 라이트·다크 자동 전환 (`prefers-color-scheme`)
- 폭 360px(모바일) ~ 1,200px에서 깨지지 않을 것
- 논문 수가 0인 교수: gray `조사 중` 태그, "수집된 논문이 없습니다"

## 3. 데이터

### 3.1 출처
| 순서 | 출처 | 용도 |
|---|---|---|
| 1 | **OpenAlex API** (무료, 키 불필요. 연락처 이메일은 보내지 않음) | 주 출처. 저자 ID로 논문 조회, 피인용 수, 주제(topics) |
| 2 | DBLP | 학회 논문 보충. OpenAlex에 없는 것만 추가 |
| — | KCI(국내 학술지) | 이번 범위에서 제외. 누락이 크면 2차로 추가 |

### 3.2 파일
```jsonc
// data/professors.json: 사람이 관리하는 원본
{ "id": "hong-shin", "order": 1, "name": "홍신", "dept": "software",
  "lab": "홍신 연구실", "emoji": "🧪",
  "openalex": ["A5xxxxxxx"],      // 사람이 확인해서 고정. 여러 개 가능 (ID 분열 대비)
  "affiliation_filter": false,     // true: 충북대 소속 표기 논문만 (섞인 프로필용)
  "field_filter": false,           // true: 컴퓨터과학 분야 논문만 (다른 분야 공동연구가 섞인 프로필용)
  "dblp": "xxx/1234",             // 선택
  "summary": "카드 하단 설명 2줄",
  "categories": [
    { "key": "fuzzing", "ko": "퍼징 테스트", "en": "Fuzz Testing", "color": "blue",
      "desc": "버그를 일으키는 입력을 자동 생성해 결함을 찾는다",
      "match": ["fuzz", "fuzzing", "crash"] }   // 논문 자동 태깅용 키워드
  ] }

// data/papers.json: 스크립트가 관리
{ "id": "W123…", "prof": ["hong-shin"], "title": "…", "year": 2025,
  "authors": ["…"], "venue": "…", "doi": "10.…", "cited": 3,
  "cats": ["fuzzing"], "source": "openalex",
  "added_at": "2026-10-26", "status": "new" }   // new | normal

// data/updates.json: 실행 기록
[{ "run_at": "2026-10-26T00:00Z", "new": 2, "by_prof": {"hong-shin": 2}, "errors": [] }]
```

### 3.3 신규 판정 규칙
- **"신규"는 출판일이 아니라 "우리가 처음 발견한 날(`added_at`)" 기준이다.** OpenAlex는 색인이 늦게 되는 경우가 있어서, 출판일 기준이면 놓치는 논문이 생긴다.
- `added_at`이 7일 이내이면 `new`, 지나면 `normal`.
- **첫 수집은 전부 `normal`로 넣는다.** 5년치 수백 편이 한꺼번에 "신규"로 뜨는 것을 막기 위해서다.
- 중복 제거 순서: DOI → OpenAlex ID → (정규화한 제목 + 연도).
- 공동 저자 교수가 2명 이상이면 논문 1건에 `prof` 배열로 묶는다.

### 3.4 카테고리
1. 교수별 5년치 논문의 OpenAlex topics와 키워드를 모은다.
2. 그걸 바탕으로 제가 카테고리 3개 초안(한글명, 영문명, 설명, 매칭 키워드)을 작성한다.
3. **사용자가 검토·수정**한 뒤 `professors.json`에 확정한다.
4. 새 논문은 제목·초록이 `match` 키워드에 걸리는 카테고리로 자동 태깅한다. 안 걸리면 태그 없이 둔다.
- 색 배정: 분야별로 고정한다 (SW공학·테스트 blue, AI·ML purple, 보안 orange, 네트워크·IoT green, DB·데이터 yellow, 시스템 brown, HCI·그래픽스 pink, 기타 gray). red는 신규 전용.

## 4. 자동화

```yaml
# .github/workflows/weekly.yml
on:
  schedule: [{ cron: "0 0 * * 1" }]   # 매주 월 09:00 KST
  workflow_dispatch: {}                # 수동 실행 버튼
jobs:
  update:
    steps:
      - fetch_papers.py   # OpenAlex/DBLP → papers.json, updates.json
      - build.py          # 데이터 인라인 → dist/index.html
      - git commit data/  # 변경 이력이 저장소에 남음
      - deploy Pages      # dist/ 배포
```
- 실패해도 기존 데이터는 지우지 않는다. 오류는 `updates.json`의 `errors`에 남기고 Actions를 실패로 표시한다(GitHub이 메일로 알림).
- 한 교수의 API가 실패해도 나머지 교수는 계속 진행한다.

## 5. 저장소 구조
```
cbnu-papers/
├── data/            professors.json · papers.json · updates.json
├── scripts/         fetch_papers.py · build.py · push_notion.py(2단계)
├── src/             template.html · app.js · tokens.css(디자인 가이드에서 복사)
├── tests/           중복 제거, 신규 판정, 태깅, 빌드 결과물에 외부 URL 없음
├── docs/            명세·조사 문서
├── dist/            빌드 결과 (Pages 배포 대상, git 제외)
└── .github/workflows/weekly.yml
```
- Python 3.11 표준 라이브러리만 쓴다(`urllib`, `json`). 설치할 패키지가 없다.

## 6. 작업 순서

| 단계 | 내용 | 사용자 확인 |
|---|---|---|
| M1 | **교수 18명 OpenAlex 저자 ID 찾기.** 학과 홈페이지에서 영문 이름 확인 → 후보 ID와 근거(소속, 대표 논문 3편) 표로 정리 | ✅ ID 표 승인 |
| M2 | `fetch_papers.py` + 테스트 → 5년치 초기 수집 | 교수별 논문 수 확인 |
| M3 | 카테고리 초안 15명분 | ✅ 문구·색 검토 |
| M4 | `build.py` + 화면 (시안 기준, 상세 화면 포함) | ✅ 화면 확인 |
| M5 | GitHub 저장소 · Actions · Pages 연결, 수동 실행 1회 | 배포 주소 확인 |
| M6 | Notion 페이지에 embed (1단계 완료) | ✅ Notion에서 확인 |
| M7 | (선택) HTML 블록 테스트 3종 → 통과하면 `push_notion.py`로 2단계 전환 | |

## 7. 완료 기준
- [ ] 18명 모두 카드가 있고, 논문이 있는 교수는 카테고리 3개 이하가 확정됨
- [ ] 수동 실행 시 새 논문이 `new`로 들어가고, 7일 뒤 `normal`로 바뀜 (날짜를 조작한 테스트로 검증)
- [ ] 같은 논문이 두 번 들어가지 않음
- [ ] 빌드된 HTML에 외부 URL 요청이 0개 (DOI 링크 `<a href>`는 예외)
- [ ] 라이트·다크, 360px·1,200px에서 깨짐 없음
- [ ] 매주 월요일 자동 실행이 돌고 Pages가 갱신됨

## 8. 리스크
| 리스크 | 대응 |
|---|---|
| 동명이인·영문 표기 차이 (Shin Hong / Hong Shin) | M1에서 사람이 ID 확정. 이름 검색은 쓰지 않음 |
| OpenAlex에서 저자 ID가 여러 개로 쪼개짐 | `openalex` 필드를 배열로 둠 |
| 국내 학술지 누락 | 교수별 수집 결과를 학과 홈페이지 업적과 비교해 보고, 차이가 크면 KCI 추가 |
| 이종연 교수님 데이터 부족 | 0편이면 "조사 중" 상태로 표시 |
| GitHub Pages 무료 플랜은 공개 저장소 필요 | 데이터가 공개 논문 정보뿐이라 공개 저장소로 진행 |
