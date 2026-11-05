## Format `code`

Each choice has a complete program in `exec_spec`. The programs run offline with `langchain`, `langchain-core` and `langgraph`. The module `fakes` provides `GenericFakeChatModel` and `ToolCallingFakeChatModel` (scripted chat models; `bind_tools` returns the same model). Network access raises `NetworkBlockedError`. A program that runs longer than 30 seconds ends with `error_type` `timeout`.

- `exec_predictions`: for every choice, predict from the document what its program does: `ok` (no uncaught exception), the exact `stdout` (print adds a trailing newline), and `error_type` (exception class name, or null). Predict each program on its own; do not assume the answer key is right.
- `answer_key_correct`: the predicted behavior of the answer-key program is what the stem asks for, and no other program matches the stem.
- `explanation_correct`: also false if a paragraph states output or an error that differs from your prediction.
- Leave `missing_variants` empty.
