# MVP 완료 조건 점검표

상태: 확정 (2026-11-05, 사용자 확인)
측정일: 2026-11-05
대상 DB: `data/quiz.db`
대상 풀: `ps_326384fb5422`(최신 풀 스냅샷, `pool_snapshots.created_at` 2026-11-05T04:53:15Z)
근거: [SERVICE.md](../../../SERVICE.md) 4.1, [requirements.md](../../01-requirements/output/requirements.md) 7.1, TASKS.md T6.3

## 요약

| # | 조건 | 결과 | 판정 |
| --- | --- | --- | --- |
| 1 | 검증 통과 문제 60개. 버킷당 10개, 형식마다 10개 이상 | 60개. 버킷 6개 모두 10. 형식 code 11, multi 14, short 17, single 18 | 충족 |
| 2 | 결정적 게이트 100%: 인용 원문 일치, 영·한 매핑 존재, 코드형 Judge-실행 불일치 0 | 60문항 마지막 시도 중 게이트 실패 0. 인용 60/60, 매핑 60/60, 코드형 실행 일치 11/11 | 충족 |
| 3 | 본인 감사 통과: 정답 키 오류 ≤ 1, 인용 미지지 ≤ 2, 매핑 불충실 ≤ 2(20문항 중) | `au_326384fb5422` `pass`. 기록 20문항. 정답 키 오류 0, 인용 미지지 0, 매핑 불충실 1 | 충족 |
| 4 | 통과 풀에서 3세트를 풀고 모든 오답에 태그 | 서버 재시작 뒤 10행 세트 3개(set_no 7, 8, 9). 태그 없는 오답 0행. 세그먼트 없는 `reading` 0행 | 충족 |

## 측정 쿼리

쿼리의 `:ps`는 `ps_326384fb5422`다. SQLite에서 그대로 돌린다.

### 조건 1

```sql
-- 풀의 passed 문제 수: 60
SELECT COUNT(*) FROM pool_snapshot_items i JOIN questions q USING(question_id)
WHERE i.pool_snapshot_id = :ps AND q.status = 'passed';

-- 버킷별: 6개 버킷 모두 10
SELECT q.bucket, COUNT(*) FROM pool_snapshot_items i JOIN questions q USING(question_id)
WHERE i.pool_snapshot_id = :ps AND q.status = 'passed' GROUP BY 1;

-- 형식별: code 11, multi 14, short 17, single 18
SELECT q.format, COUNT(*) FROM pool_snapshot_items i JOIN questions q USING(question_id)
WHERE i.pool_snapshot_id = :ps AND q.status = 'passed' GROUP BY 1;
```

| 버킷 | 수 |
| --- | --- |
| `rag` | 10 |
| `langgraph_basics` | 10 |
| `tool_mcp` | 10 |
| `middleware_hitl_guardrails` | 10 |
| `multi_agent` | 10 |
| `ops_quality` | 10 |

### 조건 2

문항마다 마지막 시도(`attempt_no` 최댓값) 행을 본다.

```sql
-- 게이트 실패 문항 수: 0
SELECT COUNT(*) FROM pool_snapshot_items i JOIN questions q USING(question_id)
JOIN verification_results v ON v.question_id = q.question_id
 AND v.attempt_no = (SELECT MAX(attempt_no) FROM verification_results WHERE question_id = q.question_id)
WHERE i.pool_snapshot_id = :ps
  AND (v.quote_match IS NOT 1 OR v.mapping_present IS NOT 1
       OR (q.format = 'code' AND v.exec_match IS NOT 1));

-- 항목별: 행 60, quote_match 60, mapping_present 60, 코드형 11, exec_match 11
SELECT COUNT(*), SUM(v.quote_match = 1), SUM(v.mapping_present = 1),
       SUM(q.format = 'code'), SUM(q.format = 'code' AND v.exec_match = 1)
FROM pool_snapshot_items i JOIN questions q USING(question_id)
JOIN verification_results v ON v.question_id = q.question_id
 AND v.attempt_no = (SELECT MAX(attempt_no) FROM verification_results WHERE question_id = q.question_id)
WHERE i.pool_snapshot_id = :ps;
```

### 조건 3

```sql
-- au_326384fb5422 | pass | 0 | 0 | 1 | 20
SELECT a.audit_id, a.result, SUM(r.answer_key_error), SUM(r.quote_unsupported),
       SUM(r.mapping_unfaithful), COUNT(r.question_id)
FROM audits a LEFT JOIN audit_records r USING(audit_id)
WHERE a.pool_snapshot_id = :ps GROUP BY a.audit_id;
```

### 조건 4

서버를 다시 시작한 뒤 돌렸다(T6.2 확인).

```sql
-- 10행인 세트 수: 3
SELECT COUNT(*) FROM (
  SELECT a.set_id FROM attempts a JOIN quiz_sets s USING(set_id)
  WHERE s.pool_snapshot_id = :ps GROUP BY a.set_id HAVING COUNT(*) = 10);

-- 태그 없는 오답: 0
SELECT COUNT(*) FROM attempts a JOIN quiz_sets s USING(set_id)
WHERE s.pool_snapshot_id = :ps AND a.correct = 0 AND a.mistake_tag IS NULL;

-- confused_segment_id 없는 reading 행: 0
SELECT COUNT(*) FROM attempts a JOIN quiz_sets s USING(set_id)
WHERE s.pool_snapshot_id = :ps AND a.mistake_tag = 'reading' AND a.confused_segment_id IS NULL;
```

| set_no | set_id | 행 | 정답 | 오답 | `reading` | `concept` |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | `s007-6208763c` | 10 | 1 | 9 | 2 | 7 |
| 8 | `s008-18acd639` | 10 | 5 | 5 | 1 | 4 |
| 9 | `s009-8e009d6e` | 10 | 2 | 8 | 0 | 8 |

## 기준선 지표

`uv run quiz metrics`가 [`data/metrics/baseline.json`](../../../data/metrics/baseline.json)을 쓴다(SERVICE.md 4.2). 2026-11-05 측정값:

| 지표 | 값 |
| --- | --- |
| Judge 통과율 | 204 / 209 = 0.9761 |
| 버린 문제 | 55(duplicate 27, regen_exhausted 17, version_conflict 11) |
| 세트별 정답률 | 세트 7 0.1, 세트 8 0.5, 세트 9 0.2 |
| 배치 | 15개. 토큰·비용·초는 파일에 있다 |
