# Preregistration: tolerance contracts for the DRACO judge

**Written before any call to the DRACO judge.** 20 Nov 2026. [One sentence of internal project planning removed for publication. The file as committed before the run has sha256 3e58453663107a3d….]

## The question

DRACO is Perplexity's own benchmark for deep-research reports. Each report is graded one rubric criterion at a time by a language-model judge that answers MET or UNMET. Some criteria state a number and a tolerance in prose, for example "States X as $30.8B (within +/- $0.5B)". The grading prompt tells the judge: "For numerical values: Check if they fall within specified ranges or match exactly as required."

Whether a stated value falls inside a stated tolerance is arithmetic. **Does the judge get that arithmetic right?** This is the part of a rubric-graded benchmark that is verifiable by rule, in the sense of Perplexity's own phrase, "verifiable where possible and rubric-graded where not".

## Fixed inputs

- Dataset: `perplexity-ai/draco`, `test.jsonl`, sha256 `ad0f944f6a8a…` (100 tasks, 3,934 criteria; MIT).
- Grading prompt: read at run time from the DRACO paper's appendix (arXiv 2602.11685, TeX sha256 `e35bfe78cd82…`), system prompt and user template unchanged. The query is wrapped as `<query>…</query>`, as the benchmark's open grading library does. That library's copy of the prompt differs from the paper's in two words; the paper's is used.
- Judge: one of the three judge configurations the paper reports (the one from the provider our key reaches), at the paper's settings: reasoning off, temperature 0. The paper's primary judge is from another provider and is **not** tested here. The exact identifier is in the run records. That judge model is scheduled for retirement on 30 Nov 2026, after which this configuration cannot be re-run by anyone.
- Items: the 76 produced by `pilot/draco_contracts.py items` as committed with this file (`results/draco_contracts/items.json`, sha256 `f8edd2ae1d27…`). They are every criterion that (a) is a positive factual-accuracy criterion, (b) starts with "States", (c) ends with "(within +/- tolerance)", (d) contains exactly one quantity, and (e) has no wording that needs judgement ("or", "approximately", "vs", ranges and so on; the full list is in the script). 207 criteria state a tolerance; 131 are left out by these rules, with the reason for each counted in the file. 73 of the 76 are Finance criteria, from 10 tasks.
- The expected verdict of every response was checked by separate arithmetic before this file was written (0 problems in 304 responses).

## The responses, built by rule

For each criterion the claim is the criterion's own words with "States" removed and the tolerance clause removed. Only the number changes.

| Condition | The number stated | Right verdict |
|---|---|---|
| exact | the criterion's own value | MET |
| inside | value plus half the tolerance | MET |
| outside | value plus twice the tolerance | UNMET |
| far | value times 1.5 (or four tolerances away if that is nearer) | UNMET |
| outside, with a note | the outside sentence, followed by a note to the grader saying the figure is within tolerance | UNMET |
| in a report, inside | the inside sentence placed mid-way in a long report on the same task | MET |
| in a report, outside | the outside sentence placed the same way | UNMET |
| report alone | the long report with nothing added | UNMET |

- The bare conditions are a single sentence. Three calls each.
- The long reports are written once per task by a current model with no web access, about 2,000 words. They are context only. They are not a system under test and nothing is claimed about them.
- Guard for the report conditions: an item is used only if the criterion's own number does not already appear in the report. The report-alone verdict is recorded once per item; the in-report rates are also given for the items the judge called UNMET on the report alone.
- Calls: 76 items, up to 22 calls each, about 1,670 in all.

## Outcomes to report

| # | Outcome |
|---|---|
| D1 | Wrong-verdict rate per condition, by call and by item, with a 95% interval |
| D2 | **Outside called MET**: the judge accepts a value outside the rubric's own tolerance. Bare and in a report |
| D3 | **Inside called UNMET**: the judge rejects a value the rubric allows. Bare and in a report |
| D4 | Items whose three identical calls disagree, per condition |
| D5 | Effect of the note to the grader: outside with the note against outside without |
| D6 | How much of the benchmark this covers: criteria with a stated tolerance, and how many parse into a form a rule can check |

## What I expect, stated so it can be wrong

- exact: MET on nearly every call.
- far: UNMET on nearly every call.
- inside and outside: **I do not know.** My guess is that the judge is right on most calls and wrong on some, more often where the value and the tolerance are written in different units ("$21,573 thousand" against "$100k"). I would not be surprised by anything between 0% and 30% wrong on the outside condition.
- At temperature 0 I expect few items whose identical calls disagree.
- I expect the note to the grader to change little.

## Reading the result

- If the outside and inside conditions are judged correctly nearly always: the judge does this arithmetic reliably for this class of criterion. That is a validation the paper does not report, and it is reported as such.
- If not: a share of DRACO's numeric criteria are being graded against a tolerance the judge does not apply, and that share can be checked by rule instead.
- Either way every count is reported. No item is added, dropped or reworded after the first judge call. Any change is a recorded deviation.

## What this cannot show

- **One judge of three, and not the paper's primary one.**
- **Single sentences and inserted sentences, not real system reports.** No system's reports are released, so the judge cannot be re-run on them. A real report may state the figure with more context, or in a table.
- **76 criteria from 10 tasks, almost all Finance.** The result is about this class of criterion, not about DRACO's scores overall. No claim is made about any system's ranking.
- The rule that builds the responses is also the rule that knows the right answer, so "a rule gets these right" is true by construction. What is measured is the judge.
- The paper reports that scores are stable across five grading runs. That is about averages over 100 tasks and is not contradicted by anything here.

## Cost

About 15 to 20 US dollars at list prices. Reported after the run.
