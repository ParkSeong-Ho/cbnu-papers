# cbnu-papers

충북대학교 소프트웨어학과·컴퓨터공학과 교수 18명의 최근 5년 논문을 모아 보여주고, 매주 새 논문을 자동으로 반영한다.

- 명세: [docs/00-spec.md](docs/00-spec.md)
- 디자인: Notion 제품 실측 토큰 ([docs/03-design-guideline.md](docs/03-design-guideline.md))
- 시안: [mockup/notion-card-mockup.html](mockup/notion-card-mockup.html)

## 실행

```sh
python3 scripts/fetch_papers.py   # OpenAlex → data/papers.json (주 1회)
python3 scripts/build.py          # data → dist/index.html (외부 요청 없는 HTML 1개)
python3 -m unittest discover -s tests
```

Python 3.11+ 표준 라이브러리만 쓴다.
