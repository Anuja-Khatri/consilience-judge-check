# Preregistration: does a reasoning step remove the third judge's error?

Written on 21 Nov 2026, before any call of the run.

## The question

DRACO's paper runs its third judge with reasoning disabled and temperature 0. On this study's test, that judge accepted a value just outside a criterion's stated tolerance for 27 of 76 criteria. The current judge of the paper's primary family, which reasons before it answers, accepted none.

**Is the error removed when the third judge's own reasoning is switched on?**

If yes, the difference between the two judges has a simple cause: the comparison needs a reasoning step. If no, the difference is in the model.

## What is the same as before

- **The sentences.** The tool's probes, `results/draco_product/probes.csv` (sha256 `147522f41376131e…`), at 1.1 tolerances below and 1.1 tolerances above the reference. They are the same text, byte for byte, as the third judge was sent before.
- **The judge.** The same model, named in every call record.
- **The grading prompt.** The one printed in the DRACO paper, unchanged.
- **How a reply is read.** The status field, by the same rule.
- **How verdicts are decided.** `consilience-judge-check table` and `check`.

## What is different: two new arms

| Arm | Reasoning | Temperature | Why |
|---|---|---|---|
| Paper settings (already run) | Off | 0 | The baseline |
| `reasoning_on` | On, at the smallest budget the provider allows (1,024 tokens) | Default | The question |
| `reasoning_off_default_temperature` | Off | Default | The control |

**Why a control is needed.** The provider does not accept temperature 0 together with reasoning. So switching reasoning on changes two things at once. The control changes only the temperature. It shows what that change does by itself.

**This is not a DRACO configuration.** The paper specifies reasoning disabled for this judge. Nothing here says the paper should have done otherwise.

## Size, order and stopping

One call per sentence. Three stages of 76 calls, in this order:

| Stage | Arm | Sentences |
|---|---|---|
| 1 | Reasoning on | 76, at 1.1 tolerances below |
| 2 | Control | 76, at 1.1 tolerances below |
| 3 | Reasoning on | 76, at 1.1 tolerances above |

- **Stop** when the metered spend reaches 2.00 US dollars. A stage cut short is reported as partial.
- **Not run:** the control at 1.1 tolerances above. It would take the cost past 2 dollars. The control question is asked on the side where the error is largest.
- **Expected cost:** about 1.90 US dollars (0.0094 a call with reasoning on, 0.0061 without).

**Two calls were made before this file was written**, on sentences that are not part of the run (3 tolerances out), to learn the reply format and the cost with reasoning on. Both were judged correctly. They cost one cent each. They are kept in `results/draco_reasoning/pings.jsonl` and are not part of any result. One of the two replies began with a stray tag before its answer; the status field was still read by rule.

## The baseline it is compared with

The paper-settings arm made three calls per sentence. These new arms make one. So the fair baseline is the **first** call of the paper-settings arm on each sentence, counted from the saved records before this run:

| Side | Criteria accepted on the first call | At least once in three calls |
|---|---|---|
| 1.1 tolerances below | 22 of 76 | 22 of 76 |
| 1.1 tolerances above | 9 of 76 | 10 of 76 |

## The rules, fixed now

| # | Outcome | "Removed" | "Not removed" | In between |
|---|---|---|---|---|
| R1 (primary) | Reasoning on, 1.1 below: criteria accepted | 3 or fewer of 76 | 11 or more (half the baseline) | "Reduced" |
| R2 (control) | Reasoning off at default temperature, 1.1 below | 3 or fewer | 11 or more | "Reduced" |
| R3 | Reasoning on, 1.1 above | 1 or fewer of 76 | 5 or more (half the baseline) | "Reduced" |

**How the three are read together.**

| R1 | R2 | Reading |
|---|---|---|
| Removed | Not removed | The reasoning step removes the error |
| Removed | Removed | Cannot tell reasoning from temperature |
| Removed or reduced | Reduced | Reasoning helps; how much of it is temperature is not settled |
| Not removed | Any | The difference between the two judges is not explained by the reasoning setting |

- **A stage is unreliable** if more than 4 of its 76 calls fail or cannot be read.
- **Also reported, with no rule:** for the criteria the paper-settings arm got wrong, how many each new arm gets right; any criterion that is newly wrong; what the judge writes when it is still wrong.

## My guess, written before the run

- R1: 0 to 4 accepted. I expect "removed".
- R2: 15 to 26 accepted. I expect "not removed".
- R3: 0 to 2 accepted.

I may be wrong, and the result will be reported either way.

## Limits known in advance

- **One call per sentence.** No repeats.
- **Built sentences, not real reports.**
- **76 criteria from 10 tasks, one of which holds 39.**
- **The smallest reasoning budget.** A larger one was not tried.
- **It cannot be repeated later.** The provider retires this judge on 30 Nov 2026.
