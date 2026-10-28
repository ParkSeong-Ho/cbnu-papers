# Notion HTML 블록 조사 정리

조사일: 2026-10-28

## 한 줄 요약

Notion 3.6(2026-07-01)에서 **페이지 안에서 HTML·CSS·JS를 실행하는 블록**이 생겼다. 단, **샌드박스 iframe이라 외부 네트워크 요청이 막혀 있다.** 그래서 "블록이 스스로 최신 데이터를 받아오는" 구조는 안 되고, **데이터를 HTML 안에 넣은 파일을 바깥에서 갱신해 넣어주는** 구조여야 한다.

## 1. 무엇인가

| 항목 | 내용 | 출처 신뢰도 |
|---|---|---|
| 출시 | Notion 3.6, 2026-07-01. "External Agents, HTML blocks, and more" | 공식 릴리스 노트 |
| 정체 | HTML·CSS·JS를 페이지 안에서 인터랙티브하게 실행하는 블록 | 공식 |
| 공식 예시 | ROI 계산기, 문서 기반 퀴즈, 인원 DB를 시각화한 조직도 | 공식 |
| 렌더링 방식 | **sandboxed iframe** 안에서 파일 내용을 실행 | 공식 API 체인지로그 |

## 2. 만드는 방법

| 방법 | 설명 | 비고 |
|---|---|---|
| `.html` 파일 업로드 | 단일 파일(자체 완결형)을 올림 | **가장 안정적**이라고 여러 가이드가 공통으로 언급 |
| Notion AI / Agent에게 요청 | 노트·DB 내용을 바탕으로 생성 | AI 생성은 Business 이상 요금제라는 제3자 보고 (공식 확인 안 됨) |
| `/html` 입력 후 코드 붙여넣기 | | 코드가 실행되지 않고 **글자로 보이는 경우가 잦다**는 보고 |
| **API** (2026-07-03~) | File Upload API로 `.html` 업로드 → `embed.file_upload`로 embed 블록에 붙임 | 공식 체인지로그. 블록 추가·페이지 생성·블록 수정 시 모두 가능 |
| Notion MCP | 에이전트가 MCP를 통해 생성 | 공식 체인지로그 |

> API 체인지로그 원문: *"Upload an .html file with the File Upload API and attach it to an embed block via embed.file_upload … The Notion app renders the file's contents interactively in a sandboxed iframe"*

## 3. 제약 (이 프로젝트에 결정적인 부분)

| 제약 | 내용 | 영향 |
|---|---|---|
| **외부 네트워크 차단** | fetch, 외부 스크립트, CDN, 원격 API 모두 불가 | OpenAlex를 블록 안에서 직접 호출할 수 없다 |
| 외부 리소스 | 웹폰트·이미지·라이브러리를 **전부 파일 안에 인라인**해야 함 | 차트 라이브러리를 쓰려면 인라인하거나 SVG를 직접 그려야 한다 |
| Notion 데이터 접근 불가 | 같은 워크스페이스의 페이지·DB를 읽거나 쓸 수 없음 | Notion DB를 데이터 원본으로 바로 쓸 수 없다 |
| 상태 비유지 | 새로고침하면 초기화됨 (localStorage 동작은 확인 안 됨) | 필터 선택 등은 매번 초기화된다 |
| 고정 테두리·파일명 라벨 | 블록 바깥 테두리와 `.html` 파일명 라벨은 제거하거나 스타일링할 수 없음 | 디자인에서 **겉테두리를 따로 그리면 이중 테두리**가 된다 |
| 크기 제한 | 공식 수치 없음. 약 50KB 파일은 문제없었다는 보고 | 논문 데이터를 넣으면 커지므로 테스트가 필요하다 |
| 공개 페이지 | notion.site로 공개한 페이지에서도 익명 방문자에게 실행됨 | 학과 공개용으로 쓸 수 있다 |
| 다크 모드·높이·모바일 | **공식 문서 없음** | 직접 테스트해야 한다 (03 문서에서 대응) |

## 4. HTML 블록과 Embed 블록 비교

| | HTML 블록 | Embed 블록 (URL) |
|---|---|---|
| 위치 | Notion 안에 파일로 저장 | 외부 서버 (예: GitHub Pages) |
| 네트워크 | 차단 | 허용 |
| 실시간 데이터 | 불가 | 가능 |
| 갱신 방법 | 파일을 다시 업로드 (API 가능) | 원본 사이트만 갱신하면 자동 반영 |
| 원본 사이트가 꺼져도 | 보임 | 안 보임 |

## 5. 확인되지 않은 것 (직접 테스트 필요)

- [ ] `prefers-color-scheme`이 Notion의 다크 모드 설정을 따라가는지
- [ ] 블록 높이가 내용에 맞춰 자동으로 늘어나는지, 아니면 고정 높이에 스크롤이 생기는지
- [ ] 무료·Plus 요금제에서 API로 HTML 블록을 생성할 수 있는지
- [ ] 파일 크기 상한 (논문 약 300편을 넣은 파일로 테스트)
- [ ] 블록 안 링크(DOI)를 클릭하면 새 탭으로 열리는지 (`target="_blank"` 동작)

## 출처

- [Notion 릴리스 노트 2026-07-01](https://www.notion.com/releases/2026-07-01): 공식
- [Notion API 체인지로그 2026-07-03 (notion-sdk-py 이슈에 인용됨)](https://github.com/ramnes/notion-sdk-py/issues/355): 공식 문구 인용
- [Notion 공식 Threads 게시물](https://www.threads.com/@notionhq/post/DaQb5qVknS2/video-new-block-in-notion-html-build-interactive-html-right-on-your-notion-page-ask)
- [mindfulsetups: HTML Block vs Embed](https://mindfulsetups.com/notion/guides/html-block-vs-embed): 제3자, 직접 테스트 기반
- [uratake (note.com): HTML 블록 기능과 주의점](https://note.com/uratake/n/n4d8b0db95198?hl=en): 제3자
- [21notion: HTML Blocks](https://21notion.com/en/notion-updates/html-blocks), [sparxno](https://www.sparxno.com/blog/notion-html-blocks), [The Organized Notebook](https://theorganizednotebook.com/blogs/blog/notion-html-block-interactive-widgets): 제3자

> 주의: 샌드박스·요금제 관련 세부 사항은 대부분 제3자 보고다. Notion 헬프센터에는 (조사 시점 기준) 전용 문서가 없다.
