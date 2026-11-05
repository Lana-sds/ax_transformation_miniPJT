# candidate-2 NOTES

Written 2026-11-05. Only `prompts/generate.md` changed. All other files under `prompts/` are byte copies of `variants/control/`.

## Changes by cause

| Cause | Change in `generate.md` |
| --- | --- |
| Model does not know how the check works | Rule 3 now says the quote must be an exact substring of the raw page source and that only whitespace runs are collapsed. So the model knows markdown counts. |
| Markdown link stripped (``[`MessagesState`](/oss/...#messagesstate)`` to `` `MessagesState` ``) | Prefer plain prose with no links, backticks or `**`. If the span has markup, keep all of it, with a link example. Avoid first, copy whole second. |
| Code fence line shortened (```` ```python theme={...} ```` to ```` ```python ````) | To quote code, copy lines from inside the fence and leave out the fence line. The long `theme={...}` line never enters a quote. |
| Unknown: rewording, omission, table cleanup, list joins | One contiguous passage of 30 to 300 characters within one paragraph, list item, table row or code block, usually the one sentence that supports the answer (control said "one or two full sentences"). Shorter, single-block spans leave fewer characters to drift. Keep list markers and `|` pipes. Do not fix typos, change case, punctuation or quote marks, or add a final period. |
| Quote rules sit far before the long documents | New closing section `## Before you answer` after `{{documents}}`: find each quote in its page and compare character by character; if anything differs, copy again or pick a plain-prose sentence. Uses recency. |

Kept as is: all placeholders, rules 1, 2, 4 to 8, the quality phrases, the "no ellipsis, no paraphrase" rule, English questions and Korean explanation, quotes only from official documents. Schema not touched.

Risk: "usually one sentence" may give the Judge a shorter quote to check `quote_supports_answer` against. The rule still says the sentence must support the answer, and several records are allowed.

## Length

| File | control | candidate-2 | ratio |
| --- | --- | --- | --- |
| `generate.md` (CRLF, as stored) | 2381 B | 3078 B | 1.293 |
| `generate.md` (LF-normalized) | 2337 B | 3026 B | 1.295 |

Limit is 1.3. Line endings kept CRLF like the control.

## Checks run

- Rendered with `quiz.pipeline.prompts.render` pointed at `candidate-2/prompts` (format `single`, quality `choice`): no `{{` left; the test phrases are present.
- No model call made.
