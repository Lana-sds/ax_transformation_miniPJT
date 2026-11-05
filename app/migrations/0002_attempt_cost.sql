-- 0002_attempt_cost: 시도 행에 비용을 둔다(T2.8).
-- 생성과 Judge 모델 단가가 다를 수 있어 합계 토큰만으로는 배치 비용을 계산할 수 없다.
-- 단가가 없는 모델을 쓴 시도는 NULL이다. batches.cost_usd는 배치의 시도 행 비용이 모두 있을 때 그 합이다.

ALTER TABLE verification_results ADD COLUMN cost_usd REAL;
