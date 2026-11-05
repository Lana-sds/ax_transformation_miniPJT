## Choice quality

Also check these two items. They apply to every format with choices. Judge the wording only; these items are false even when the answer key is correct.

- `distractors_plausible`: every wrong choice carries a misconception a developer could really hold (for example a fix that only removes the symptom, or a correct pattern applied in the wrong context). False if any wrong choice makes no sense, is obviously unrelated, or is too vague to be a real belief.
- `no_cue`: a learner who has not read the document cannot find the answer from the wording alone. Run each test below. If any test hits, `no_cue` is false and `reasons` names the test.
  1. Length: count the words of each choice. The correct choice (any correct choice for several answers) has more than 1.5 times the words of the longest wrong choice.
  2. Absolute words: a wrong choice contains only, always, never, all or none, and no correct choice does.
  3. Echo: the correct choice repeats a distinctive word or phrase from the stem that no wrong choice uses.
  4. Odd one out: the correct choice differs from all wrong choices in form (for example it is the only one with a reason clause, a qualifier, or a code name).
  5. Stem leak: the stem already shows the correct code or API name, or spells it out in words.
  6. Copied wording: only the correct choice copies a document sentence nearly word for word.
