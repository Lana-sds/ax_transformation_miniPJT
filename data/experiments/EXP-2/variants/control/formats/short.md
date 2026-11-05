## Format `short`

- No choices. The learner types the answer.
- The answer is a single API, class, function or parameter name, or a single term, exactly as the document writes it. Never a phrase or a sentence.
- `answer_key` is a list with that one canonical answer.
- `accepted_answers`: 1 to 5 spellings that must be graded correct, including the canonical answer (for example `add_node` and `StateGraph.add_node`). Grading ignores case, backticks, whitespace and one trailing `()`, so do not list those variants.
- The stem must make the expected kind of answer clear, for example "Which method ...? Answer with the method name."
