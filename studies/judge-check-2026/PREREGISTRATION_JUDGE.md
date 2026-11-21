# Judge arm preregistration: how does the benchmark's explanation judge score explanations whose structure is known?

**Written before any call to a judge.** 20 Nov 2026. This arm has not been run: it needs a key for the judge's provider.

## The question

The benchmark passes a run only if a language-model judge gives the written explanation a high enough score. How often does that judge pass an explanation that states the wrong law, and how much does its score for the same text change between identical calls?

## Fixed inputs

- Benchmark: `SampsonML/DiscoverPhysics`, commit `33b7fa9df96d`. The judge is called through the benchmark's own `ExplanationJudge`, with its prompt, its per-world rubric and its reference explanation, and its default judge model.
- Worlds: gravity, yukawa, coulomb_easy, extra_dimensions, oscillator. The `fractional` world is left out of the counts because its rubric contradicts its simulator (an outside reviewer has filed a fix on the benchmark's repository).
- Texts: the 53 explanations produced by `pilot/judge_arm.py --list` as committed with this file.
  - `right_structure`: the benchmark's own reference text; a textbook-style text with every typed field correct; a plain-words text with every field correct and no operator names.
  - `wrong_structure`: the textbook-style text with exactly one typed field changed (decay, sign, roles, time, and where defined one parameter off by a factor of ten); the wrong-decay text followed by a note addressed to the grader; the reference text of a different world; a text with the operator's name and no commitments.
- Repeats: 5 calls per text, 265 calls in total.
- Pass marks: raw score 8 or more (the public code's 0.75) and 9 or more (the paper's 0.9).

## Outcomes to report

| # | Outcome | Reported as |
|---|---|---|
| J1 | Wrong-structure texts that pass | Calls passing out of all calls, and texts passing at least once, at each pass mark, with a breakdown by which field was changed |
| J2 | Right-structure texts that fail | The same, with the plain-words texts shown separately |
| J3 | Movement between identical calls | Texts whose five scores straddle a pass mark; range of scores per text |
| J4 | The note addressed to the grader | Score of the wrong-decay text with and without the note |

## What I expect, stated so it can be wrong

- The reference text and the textbook-style correct text score 9 or 10.
- The different-world text and the vocabulary-only text score low.
- **I do not know** how the single-field errors will score. The rubrics place "asserts 1/r²" and "muddles p1/p2" in the 7 to 9 band, and both pass marks fall inside that band, so some passes would follow from the rubric as written and would not be a judge error.
- I expect at least some texts to straddle a pass mark across five calls, because no temperature is set and the score is a whole number.

## Reading the result

- If single-field errors rarely pass and scores barely move: the judge is sound on these texts. That is the validation the benchmark's authors said was missing, and it is reported as such.
- If they pass often: the explanation half of the pass rule does not separate a right law from a wrong one stated in the right vocabulary.
- Either way the counts are reported in full. No text is added, dropped or reworded after the first call. Any change is a recorded deviation.

## What this arm cannot show

- The texts are written by rule, not by agents. Real explanations are messier.
- One judge model unless others are added, in which case each is reported separately.
- A pass caused by the rubric's own bands is a property of the rubric, not of the judge.
