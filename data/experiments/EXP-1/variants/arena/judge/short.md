## Format `short`

The learner types the answer. `accepted_answers` lists the spellings that count as correct. Grading ignores case, surrounding spaces and a trailing `()`.

- `answer_key_correct`: the canonical answer is the one term the stem asks for. False if another document term also fits, or the stem contains the answer or spells out its name ("adds a node" for `add_node`).
- `missing_variants`: other spellings of the same answer that a learner who knows the document would type and that `accepted_answers` lacks, for example the qualified name (`StateGraph.add_node`) or the import path. Do not add different answers. Leave it empty when nothing is missing. Leave `exec_predictions` empty.
