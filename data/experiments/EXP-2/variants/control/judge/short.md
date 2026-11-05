## Format `short`

The learner types the answer. `accepted_answers` lists the spellings that count as correct. Grading ignores case, surrounding spaces and a trailing `()`.

- `answer_key_correct`: the canonical answer is the one term the stem asks for.
- `missing_variants`: other spellings of the same answer that a learner who knows the document would type and that `accepted_answers` lacks, for example the qualified name (`StateGraph.add_node`) or the import path. Do not add different answers. Leave it empty when nothing is missing. Leave `exec_predictions` empty.
