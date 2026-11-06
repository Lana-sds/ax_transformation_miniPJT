# web: agent-dev-quiz 화면

React + Vite(TypeScript) 화면이다. 문제 풀이, 결과·해설, 오답 태그, 감사 화면(`#audit`)이 있다. 데이터는 API 서버(`app/`)에서 받는다.

## 실행

1. API 서버를 먼저 띄운다(`app/`에서). 제출 DB를 그대로 두려면 사본을 `QUIZ_DB`로 준다. 자세한 내용은 [루트 README](../README.md)의 "바로 실행해 보기"에 있다.

   ```bash
   cd app
   uv run uvicorn quiz.server:app --port 8000
   ```

2. 웹을 띄운다(`web/`에서).

   ```bash
   npm ci        # 처음 한 번
   npm run dev
   ```

3. `http://localhost:5173`을 연다.

개발 서버는 `/api`, `/docs`, `/scalar`, `/redoc`, `/openapi.json`을 `http://localhost:8000`으로 넘긴다(`vite.config.ts`). 그래서 CORS 설정이 없다. API 서버 포트를 바꾸면 `vite.config.ts`의 주소도 바꾼다.

## 명령

| 명령 | 용도 |
| --- | --- |
| `npm run dev` | 개발 서버(5173) |
| `npm run build` | 타입 검사(`tsc -b`)와 빌드(`dist/`) |
| `npm run lint` | oxlint |
| `node --test src/*.test.ts` | 순수 함수 테스트. Node가 TypeScript를 바로 돌린다. 화면 컴포넌트 테스트 도구는 없다 |

## 구조

| 파일 | 내용 |
| --- | --- |
| `src/App.tsx` | 세트 시작, 문제 이동, 답 제출, 충돌(409) 처리 |
| `src/ResultPanel.tsx`, `src/Evidence.tsx` | 결과, 해설, 영·한 구절 표, 근거 인용 |
| `src/TagForm.tsx` | 오답 태그(독해 실수, 개념 실수) |
| `src/AuditPage.tsx` | 감사 화면 |
| `src/formats/` | 형식별 보기 입력(단일, 복수, 단답, 코드) |
| `src/markup.ts`, `src/MarkupText.tsx` | 코드 블록, 인라인 코드, 굵게 표시 |
| `src/api.ts` | API 호출과 응답 타입 |
