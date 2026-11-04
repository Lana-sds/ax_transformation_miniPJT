# Interview ledger: interview_20261104_041911 (LangChain pack MVP)

Goal: personal LLM study web app. Generates English expected-exam questions on LLM app development with LangChain/LangGraph, grounded only in verbatim official-doc quotes; Korean explanations with phrase-level EN-KO mapping; wrong answers tagged reading vs concept mistake and fed to a review queue. Target user: Korean LangChain/LangGraph developer who will later take CCA-F (end of Nov 2026). First user = author. CCA-F pack is a later pack.

## Scope
- Pack: LangChain first. Topic buckets day2 RAG, day3 LangGraph basics, day4 Tool/MCP, day5 middleware/HITL/checkpointer, day6 multi-agent, day7 operations/eval. day1 excluded. Each question carries a related CCA-F domain tag ("none" allowed).
- Formats: single choice, multiple choice (count stated), short answer, code choice. Questions English, explanations Korean.
- Grounding: design option A (docs-langchain + reference-langchain MCP). Evidence record {page, quote, fetched_at, answer_basis}. Pipeline may only quote from an allowlist of official doc pages, built in stage 2 by mapping the ~34 topics listed in candidate_langchain.md's day2-day7 rows; frozen as repo file with page snapshots + fetch date.
- Code questions: official-doc example code first, practice repo .py second; framework behavior only.

## Architecture
- Local backend server: FastAPI + uvicorn (course precedent day6 api_server.py; added to backend env). Storage SQLite (stdlib sqlite3): solve log, per-item verdicts, pool snapshot ids, audit records. Versioned artifacts (allowlist, page snapshots, baselines) as repo files.
- UI: React, separate frontend calling FastAPI. Node v26.13.0 / npm 11.20.0 / Bun 1.4.4 present.
- Batch LangGraph pipeline on the server: generate -> judge -> code-exec -> deterministic quote-match -> regenerate (max 3 iterations per item; exhaustion = drop with reason). Pre-generated pool; sets of 10 served from pool; unlimited sets.
- Two Python envs: app backend follows course repo (sds-ax-practice; langchain/langgraph pinned at build to versions course code runs on); code-exec sandbox = docs-latest + 4 MCP pins (mcp==1.30.0, fastmcp==2.13.0, langchain-mcp-adapters==0.3.2, mcp-server-time==2026.10.10), GenericFakeChatModel (+bind_tools subclass), offline, no Bedrock in gate. Answer key follows quoted docs; conflicts dropped and counted; docs fetch date + lock hash per question.
- Models (AWS Bedrock only; available list in docs/01-requirements/input/bedrock-model-list.md): generation global.anthropic.claude-sonnet-4-6; judge global.anthropic.claude-sonnet-4-5-20250929-v1:0; fallback global.anthropic.claude-haiku-4-5-20251001-v1:0. Bedrock spend cap not set; cost logged per batch.
- Langfuse Cloud Hobby (50k units/month, 30-day window); one UI trace export on 2026-11-06; metrics/baselines also as repo files; pipeline runs with Langfuse off.
- Local only for MVP; later server deployment must not be blocked.

## Review queue
- Set-count spacing: wrong item returns +2 sets, then +5 sets. Max 3 review items per set of 10. Removed after 1 correct.
- Reading mistake -> same item returns. Concept mistake -> variant generated from stored log; variant passes same gates; else original reused. Variants stored separately (variant_of), not counted toward MVP done.
- Solve-log schema: question_id, set_id, ts, answer, correct, mistake_tag, schema_version.

## MVP done (deadline 2026-11-07, AX mini-project deadline)
- Pool: 60 accepted, 10 per bucket, each of 4 formats >= 10.
- Deterministic gates 100%: verbatim quote on allowlisted page; EN-KO mapping present; judge-vs-execution mismatch 0 on code questions.
- Human audit by the user, 20 random from frozen pool snapshot: wrong key <= 1; quote not supporting answer <= 2; questions with any unfaithful EN-KO mapping <= 2.
- User solves 3 sets from the accepted pool; every wrong answer tagged.
- Baselines only: judge pass rate, drop count with reason, own accuracy change.
- On miss: remove failing, backfill to 60, fresh random 20 re-audit. If still missing on 2026-11-07: NOT done; record user waiver with miss list.

## Guard-round decisions (user-approved)
- Grading: single/multi/code choice exact match to key, no partial credit. Short answer: accepted-answers list generated and judge-verified; normalize case/whitespace; no LLM grading at solve time.
- Mistake tag: user picks reading vs concept on the wrong-answer screen; reading mistake also selects the confusing English phrase. No auto tagging.
- Pool exhaustion: after 6 sets, sets filled with review items + previously correct items; more batches by manual command.
- Set composition: >=7 new items random across topics/formats, <=3 review items.
- Cut line: if <30 accepted by evening 2026-11-05, cut (1) variant generation, (2) Langfuse export, (3) pool target to 30 (5/bucket) with user waiver. React UI kept.
- Answer keys follow latest docs for all questions; cross-version-conflicting code questions dropped.
- Deferred to stage 2: quote normalization rules, audit random seed, Bedrock retry/spend cap, CORS, near-duplicate detection.

## Known risks / open items
- Per-question generation time unmeasured; 3-day deadline includes spec, pipeline, server, React UI, allowlist curation, 60 questions, audit, 3 sets.
- Bedrock spend cap open. Exact page allowlist built in stage 2.
- tech-stack-common.md still says "Bedrock 경유 Claude"; CLAUDE.md updated.
