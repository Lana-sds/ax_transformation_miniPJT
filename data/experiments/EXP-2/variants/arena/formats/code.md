## Format `code`

- Exactly four choices with ids A, B, C, D. Each choice is a short Python snippet in `code` (no `text`). Exactly one is correct.
- The stem describes a behavior or an error, for example "Which snippet prints `['a', 'b']`?" or "Which snippet raises `InvalidUpdateError`?"
- `exec_spec`: one entry per choice. `code` is a complete program that runs offline as is: all imports, no network, no API keys, no files, no input(), finishes within a few seconds.
- Chat models: never import a real provider model. Use only the fakes from the sandbox module `fakes` described below.
- `expected` is what the program does according to the documents: `ok` (no uncaught exception), the exact `stdout` (print adds a trailing newline), and `error_type` (exception class name, or null). The correct choice's `expected` must match what the stem asks for, and the other choices' must not.
- Base the behavior only on what the documents state. Do not test undocumented edge cases or exact exception messages.

{{fakes}}
