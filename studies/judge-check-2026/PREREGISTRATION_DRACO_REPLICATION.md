# Preregistration: DRACO judge, replication arm

**Written and committed before any call in this arm.** 20 Nov 2026. Follows `PREREGISTRATION_DRACO.md` and `PREREGISTRATION_DRACO_BOUNDARY.md`. Same dataset, same grading prompt, same judge and settings, same 76 criteria (`results/draco_contracts/items.json`, sha256 `f8edd2ae1d27…`, unchanged).

## Why this arm exists

[One sentence naming a person removed for publication. The file as committed before the run has sha256 b0a7dc2c3ede586f….] Checking the near-boundary figure against the raw records, before any new call, gave three answers.

1. **The count is right.** 26 of 228 calls returned MET for a value 1.1 tolerances above the reference. Recounted from `judge_calls.jsonl`.
2. **The errors are not a matter of reading.** In all ten criteria concerned, the judge's own reply writes out the allowed range, or the size of the gap, and then says a number outside it is inside. Example: "states … $66.2M, which falls within the acceptable range of $64M +/- $2M ($62M to $66M)".
3. **The way it was reported was too strong, in two ways.**
   - The three calls on one criterion are made at the paper's setting for this judge, which is nearly deterministic. They are not three independent trials. The honest unit is the criterion: **10 of 76 criteria** (13%, 95% interval 7% to 23%). The interval quoted before (7.9% to 16.2%, on 228 calls) was too narrow.
   - It came from a follow-up arm designed after the first results, tested values above the reference only, and used single sentences only.

This arm addresses the second point of 3 with responses the judge has not been shown. The first point is corrected in every write-up whatever this arm finds.

## Conditions

Built by rule (`pilot/draco_replication.py items`), written to `results/draco_replication/items_replication.json` (sha256 `93b825671af0d711…`). Each response's right verdict was checked by separate arithmetic that reads the number back out of the sentence: 0 problems in 297 responses. None of the 228 single sentences has been shown to the judge before.

| Condition | The number stated | Right verdict | Criteria | Calls each |
|---|---|---|---|---|
| below, just outside | value minus 1.1 tolerances | UNMET | 76 | 3 |
| below, just inside | value minus 0.9 tolerances | MET | 76 | 3 |
| above, further out | value plus 1.5 tolerances | UNMET | 76 | 3 |
| in a report, just outside | value plus 1.1 tolerances, placed as its own paragraph in the long report used in the first arm | UNMET | 69 | 1 |

- The in-report condition uses the 69 criteria whose report the judge called UNMET on its own in the first arm, so the inserted sentence is the only place the figure appears. One call each, because repeats at this setting add little and these calls are long.
- 753 calls. Call records go to `results/draco_replication/judge_calls.jsonl`. Nothing in the first arms' folder is written to.

## Outcomes and decision rules, fixed now

The unit is the criterion. A criterion counts as wrong if any of its calls gives the wrong verdict. Counts by task (10 tasks) are reported beside it.

| # | Question | Rule fixed in advance |
|---|---|---|
| R1 (primary) | Does the judge accept a value just outside the tolerance on new responses? | **Replicated** if the judge returns MET on at least 4 of the 76 criteria in "below, just outside". **Not replicated** if 3 or fewer |
| R2 | Do the errors gather at the boundary? | Holds if fewer criteria are wrong at plus 1.5 tolerances than the 10 at plus 1.1. If 10 or more are wrong, "errors gather at the boundary" is withdrawn |
| R3 | Does it happen inside a long report, where real grading happens? | Shown if at least 4 of the 69 criteria are accepted. If 3 or fewer, the write-up says the leniency was shown for single sentences only |
| R4 | The strict side: does the judge refuse a value just inside? | Reported as counted. The first arm had 5 of 76 criteria |
| R5 | Are the errors self-contradictions? | Every wrong reply is read. Reported: how many state a range or gap that contradicts the verdict given. Every such reply stays in the call record for anyone to read |

Why 4: if the true share of criteria were the 13% seen above the reference, 3 or fewer of 76 would be very unlikely (probability about 0.007). If it were the 1 in 76 seen at two tolerances out, 4 or more would be unlikely too (about 0.018).

## What changes in the write-ups, by outcome

| Outcome | What the write-ups will say |
|---|---|
| R1 replicated | The near-boundary result is reported as replicated on new responses, with the criterion counts from both sides and the pooled count of criteria wrong on either side |
| R1 not replicated | The near-boundary result is removed from the summary. It is reported lower down as seen once, above the reference only, and not replicated. The public study does not go out with it as a finding |
| Either | Call percentages are no longer the headline. Criterion counts and criterion-level intervals are. The number of tasks is stated |

## Expectations, stated so they can be wrong

- R1: I expect between 5 and 15 of 76 criteria.
- R2: I expect between 1 and 5 of 76 criteria at plus 1.5 tolerances.
- R3: I expect at least 4 of 69, on the reasoning that a long context does not make the comparison easier. I am less sure of this one: the first arm's in-report rate at two tolerances was only slightly above the single-sentence rate.
- R4: I expect between 2 and 10 of 76.
- R5: I expect at least 8 in 10 wrong replies to contradict themselves.

## Limits that this arm does not remove

- **One judge of three, and not the paper's primary one.** The paper's primary judge and its second judge come from two other providers and are not tested. Nothing here says they share the behaviour.
- **The same 76 criteria.** These are all the criteria in the benchmark that state a tolerance and pass the parsing rules. The arm replicates the judge's behaviour on new values, not on new criteria. They come from 10 tasks, mostly Finance.
- **Built sentences.** A value stated to more decimal places than a real report would use is a test of the comparison, not of typical reports.
- The judge tested is to be retired by its provider on 30 Nov 2026. After that this arm cannot be re-run on it.

Cost: about 5 US dollars.
