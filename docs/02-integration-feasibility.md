# 논문 모아보기 × Notion HTML 블록: 결합 가능성 판단

작성일: 2026-10-28 · 전제: 01-notion-html-block.md

## 결론

**가능하다. 단, "Notion이 데이터를 받아오는" 방식이 아니라 "GitHub Actions가 매주 HTML을 새로 만들어 Notion에 밀어 넣는" 방식이어야 한다.**

HTML 블록은 네트워크가 막혀 있어서 블록 안에서 OpenAlex를 호출할 수 없다. 대신 2026-07-03부터 API로 HTML 블록을 만들고 교체할 수 있으므로, 주간 수집과 Notion 반영을 같은 파이프라인 하나로 묶을 수 있다.

## 확정된 요구사항 (사용자 답변 반영)

| 항목 | 결정 |
|---|---|
| 실행 환경 | GitHub 저장소 + GitHub Actions |
| 대상 | 15명 전원 (이종연 교수님 포함) |
| 초기 수집 범위 | 최근 5년 (2021~) |
| 정부과제 | 제외 |
| 최종 노출 | Notion 페이지 |

## 구조안 3가지 비교

### A안: HTML 블록에 데이터 인라인 + API로 매주 교체 ⭐ 추천

```
[GitHub Actions, 매주 월 09:00 KST]
  fetch_papers.py ── OpenAlex/DBLP ──▶ data/papers.json (status: new/normal)
  build_html.py   ── JSON을 HTML 안 <script> 에 박음 ──▶ dist/*.html (자체 완결형)
  push_notion.py  ── File Upload API ──▶ Notion 블록 교체 (embed.file_upload)
```

- 장점: Notion 안에서 완결된다. 외부 사이트가 꺼져도 보인다. notion.site로 공개해도 실행된다.
- 단점: 블록 테두리·파일명 라벨을 없앨 수 없다. 파일 크기 상한을 모른다. 상태(필터 선택)가 유지되지 않는다.
- 필요한 것: Notion Integration 토큰을 GitHub Secrets에 저장, 대상 페이지를 Integration에 공유

### B안: GitHub Pages + Notion Embed 블록

```
Actions → papers.json 갱신 → GitHub Pages 배포 → Notion은 /embed URL로 표시만
```

- 장점: Notion API를 쓰지 않아 가장 단순하다. 크기 제한이 없다. 사이트를 단독 주소로도 쓸 수 있다.
- 단점: "노션에 적용"이라기보다 노션 안에 창을 하나 낸 것에 가깝다. GitHub Pages가 공개 저장소여야 한다(무료 플랜 기준).

### C안: Notion 데이터베이스를 원본으로 + HTML 블록은 요약 뷰

```
Actions → Notion API로 "논문 DB"에 행 추가 (status 속성 = 신규/일반)
       → 동시에 요약 HTML(교수 카드)을 블록으로 교체
```

- 장점: 논문 목록은 Notion 기본 DB 뷰(필터·정렬·검색)를 그대로 쓴다. 신규 표시도 DB 속성으로 처리된다.
- 단점: API 호출이 가장 많고 구현량이 제일 크다. HTML 블록은 DB를 읽지 못하므로 같은 데이터를 두 군데에 쓰게 된다.

### 비교표

| 기준 | A 인라인 HTML | B Embed | C DB + HTML |
|---|---|---|---|
| Notion다움 | ◎ | △ | ◎ |
| 구현 난이도 | 중 | **하** | 상 |
| 주간 자동 갱신 | ○ (API 교체) | ○ (Pages 재배포) | ○ |
| 외부 의존 | Notion API | GitHub Pages | Notion API |
| 확인 안 된 리스크 | 파일 크기, 높이, 다크 모드 | 거의 없음 | API 호출 한도 |

## 추천: **B로 먼저 시작 → A로 이전 (같은 HTML 재사용)**

1. **1단계 (B):** 정적 사이트를 GitHub Pages로 먼저 띄우고 Notion에는 embed로 붙인다. 디자인과 데이터 품질을 여기서 검증한다.
2. **2단계 (A):** 빌드 단계에서 JSON을 HTML 안에 인라인한 "Notion 전용 빌드"를 하나 더 만들고, API로 HTML 블록을 교체한다.
3. **처음부터 HTML을 자체 완결형으로 만든다.** 외부 CDN·웹폰트를 쓰지 않으면 1단계 결과물이 2단계에 그대로 들어간다. 그래서 03 디자인 가이드에 "외부 요청 0개" 규칙을 넣었다.

## 2단계 전에 직접 확인할 테스트 (30분 정도)

1. 테스트 페이지에 `mockup/notion-card-mockup.html`을 업로드한다 → 렌더링·높이·다크 모드를 본다.
2. 더미 논문 300편을 인라인한 HTML(예상 200~400KB)을 올린다 → 크기 상한을 확인한다.
3. Notion Integration으로 `embed.file_upload` 교체를 한 번 수동 호출한다 → 요금제 제한을 확인한다.

세 가지가 모두 통과하면 A안으로 넘어간다. 하나라도 막히면 B안으로 유지한다.

## 리스크

| 리스크 | 대응 |
|---|---|
| 동명이인 때문에 엉뚱한 논문이 섞임 | 교수별 OpenAlex 저자 ID를 사람이 1회 확인해 고정 |
| 국내 학술지(KCI) 누락 | OpenAlex + DBLP로 시작하고, KCI는 2차 과제로 |
| 이종연 교수님 데이터 부족 (목록에서 흐리게 표시된 상태) | 조사 후 논문이 0~소수면 카드에 "데이터 부족" 상태 표시 |
| Notion HTML 블록 사양 변경 (공식 문서 없음) | B안을 언제든 대체 경로로 유지 |
