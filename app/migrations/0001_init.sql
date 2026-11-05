-- 0001_init: design.md 5.1 스키마.
-- JSON 열은 TEXT에 JSON을 담는다. 시각은 ISO 8601 UTC 문자열이다.

CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);

CREATE TABLE batches (
  batch_id TEXT PRIMARY KEY,               -- b20261105-01
  kind TEXT NOT NULL CHECK (kind IN ('pool', 'variant')),
  started_at TEXT NOT NULL, finished_at TEXT,
  gen_model TEXT NOT NULL, judge_model TEXT NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL                             -- 단가표로 계산, 단가 없으면 NULL
);

CREATE TABLE batch_slots (
  batch_id TEXT NOT NULL REFERENCES batches, slot_no INTEGER NOT NULL,
  bucket TEXT NOT NULL, topic TEXT NOT NULL, format TEXT NOT NULL, question_type TEXT NOT NULL,
  variant_of TEXT REFERENCES questions,     -- 변형 배치만
  question_id TEXT NOT NULL UNIQUE,
  PRIMARY KEY (batch_id, slot_no)
);

CREATE TABLE questions (
  question_id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL REFERENCES batches,
  bucket TEXT NOT NULL, topic TEXT NOT NULL,
  format TEXT NOT NULL,                     -- single | multi | short | code. CHECK 없음(NFR-1.2)
  question_type TEXT NOT NULL,              -- concept | code_behavior | error_cause | design. CHECK 없음
  select_count INTEGER,                     -- multi만
  cca_f_tag TEXT NOT NULL,                  -- 'n/a' 허용
  stem_en TEXT NOT NULL,
  choices_json TEXT,                        -- [{id, text}] 또는 [{id, code}]
  answer_key_json TEXT NOT NULL,            -- ["B"] 또는 ["A","C"] 또는 단답 대표 답
  accepted_answers_json TEXT,               -- 단답만, 최대 5개
  explanation_ko TEXT NOT NULL,
  segments_json TEXT NOT NULL,              -- [{segment_id, en, ko}]
  exec_spec_json TEXT,                      -- 코드형만. 보기별 실행 코드
  doc_url TEXT,                             -- 코드형 "코드 보기" 링크
  status TEXT NOT NULL CHECK (status IN ('draft', 'passed', 'dropped', 'audit_failed')),
  drop_reason TEXT,                         -- regen_exhausted | judge_exec_mismatch | version_conflict | duplicate | ...
  regen_count INTEGER NOT NULL DEFAULT 0 CHECK (regen_count BETWEEN 0 AND 3),
  variant_of TEXT REFERENCES questions,
  fetched_at TEXT NOT NULL, lock_hash TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  CHECK (status <> 'dropped' OR drop_reason IS NOT NULL)
);

CREATE TABLE grounding_records (
  question_id TEXT NOT NULL REFERENCES questions, idx INTEGER NOT NULL,
  page TEXT NOT NULL, quote TEXT NOT NULL, fetched_at TEXT NOT NULL, answer_basis TEXT NOT NULL,
  PRIMARY KEY (question_id, idx)
);

CREATE TABLE verification_results (
  question_id TEXT NOT NULL REFERENCES questions, attempt_no INTEGER NOT NULL,  -- 0~3
  quote_match INTEGER, mapping_present INTEGER, judge_pass INTEGER, exec_match INTEGER,
  duplicate_of TEXT,
  judge_verdict_json TEXT, exec_result_json TEXT, fail_reasons_json TEXT,
  input_tokens INTEGER, output_tokens INTEGER, created_at TEXT NOT NULL,
  PRIMARY KEY (question_id, attempt_no)
);

CREATE TABLE pool_snapshots (pool_snapshot_id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
CREATE TABLE pool_snapshot_items (
  pool_snapshot_id TEXT NOT NULL REFERENCES pool_snapshots, question_id TEXT NOT NULL REFERENCES questions,
  PRIMARY KEY (pool_snapshot_id, question_id)
);

CREATE TABLE quiz_sets (
  set_id TEXT PRIMARY KEY, set_no INTEGER NOT NULL UNIQUE,   -- 복습 간격은 set_no로 센다
  pool_snapshot_id TEXT NOT NULL REFERENCES pool_snapshots,
  question_ids_json TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT
);

CREATE TABLE attempts (
  attempt_id INTEGER PRIMARY KEY,
  question_id TEXT NOT NULL REFERENCES questions, set_id TEXT NOT NULL REFERENCES quiz_sets,
  ts TEXT NOT NULL, answer TEXT NOT NULL, correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
  mistake_tag TEXT CHECK (mistake_tag IN ('reading', 'concept')),
  confused_segment_id TEXT,
  schema_version INTEGER NOT NULL,
  UNIQUE (set_id, question_id),
  CHECK (correct = 0 OR mistake_tag IS NULL),
  CHECK (mistake_tag IS NOT 'reading' OR confused_segment_id IS NOT NULL)
);

CREATE TABLE review_items (
  question_id TEXT PRIMARY KEY REFERENCES questions,          -- 원래 문제
  mistake_tag TEXT NOT NULL, review_round INTEGER NOT NULL CHECK (review_round IN (1, 2)),
  due_set_no INTEGER NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('pending', 'cleared', 'retired'))
);

CREATE TABLE audits (
  audit_id TEXT PRIMARY KEY, pool_snapshot_id TEXT NOT NULL REFERENCES pool_snapshots,
  seed TEXT NOT NULL, sample_json TEXT NOT NULL, created_at TEXT NOT NULL,
  result TEXT CHECK (result IN ('pass', 'fail'))
);
CREATE TABLE audit_records (
  audit_id TEXT NOT NULL REFERENCES audits, question_id TEXT NOT NULL REFERENCES questions,
  answer_key_error INTEGER NOT NULL, quote_unsupported INTEGER NOT NULL, mapping_unfaithful INTEGER NOT NULL,
  note TEXT, recorded_at TEXT NOT NULL,
  PRIMARY KEY (audit_id, question_id)
);
