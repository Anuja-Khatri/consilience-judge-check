# Preregistration: the DiscoverPhysics judge, two further arms

**Written before any call in these arms.** 20 Nov 2026. Follows `PREREGISTRATION_JUDGE.md` (run earlier today: 265 calls, one judge).

## Why

The benchmark's paper names two limits of its explanation judge itself: "The explanation score relies on a single LLM judge… ideally this would be averaged over multiple judge models", and the pass thresholds "are also somewhat arbitrary". The first arm tests the fix the authors propose. The second checks whether the judge scores printed in the paper come out again.

## Arm P: a panel of judges

- The same 53 rule-written texts as the first arm, unchanged (`pilot/judge_arm.py --list`, sha256 of the listing `2e32db6a5b59…`), five calls each, scored by **two further judge models** through the benchmark's own `ExplanationJudge`, prompt and rubrics. Both are from the provider our key reaches; one is stronger than the default judge and one is smaller. Identifiers are in the run records. 530 calls.
- **Limit, stated first:** the authors' suggestion is about judges from different providers. Three judges from one provider share more than three from different ones would. This arm can show whether the choice of judge moves pass and fail decisions on identical texts. It cannot show what a cross-provider panel would do.

Outcomes:

| # | Outcome |
|---|---|
| P1 | For each judge: wrong-law calls passing and right-law calls failing, at both pass marks (8 and 9) |
| P2 | For the panel (the mean of the three judges' scores, repeat by repeat, compared with the mark): the same counts |
| P3 | Texts on which the three judges' median scores differ by 2 points or more |

Expectations: I expect the other two judges to agree with the first on the reference texts and the off-topic texts. **I do not know** whether they pass the single-field errors more or less often, or whether averaging helps the plain-words texts that the first judge failed 21 times in 25 at the paper's mark.

## Arm R: the scores printed in the paper

- The eleven agent explanations printed in the paper's appendix (decoded into `pilot/paper_examples.json`), each scored five times by the benchmark's default judge with that world's rubric and reference text at commit `33b7fa9df96d`. 55 calls.
- Two TeX escapes inside two explanations were decoded to plain text (a unit vector and a square root); the rest is as printed.

Outcomes:

| # | Outcome |
|---|---|
| R1 | For each explanation: the five scores beside the printed score |
| R2 | Explanations whose pass or fail (at 8 and at 9) differs from the printed score's on any call |

Expectations: most re-scores within one point of the printed score. The rubrics may have changed between the paper's runs and this commit, so a difference is not by itself a fault in the judge; any difference is reported with that caveat.

## Reading the result

All counts reported in full. Nothing is added, dropped or reworded after the first call. Cost: about 5 US dollars.
