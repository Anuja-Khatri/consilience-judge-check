# The independent recount of the run on the second judge

On 22 Nov 2026 the run on the second DRACO judge reached its spending cap (Part 1b of the write-up). Before its final numbers were published, a separate AI session, which had not run it, was given the call records and the code, not the conclusion, and asked to recount.

- **It reproduced every count**: 703 records, 6 failed, 697 with a verdict, none wrong.
- **Its findings are about what is said around the counts**, and about what the records cannot prove. Part 1b now states them.
- **It was done by an AI session, not by a person.**

Its report is below as it was returned. Two kinds of words are replaced, and nothing else is changed: the path of its scratch folder, and model identifiers, written in square brackets.

## What was done about each finding

| # | Finding | What was done |
|---|---|---|
| 1 | The in-report result is weaker evidence than the single-sentence result: no value inside a tolerance was placed in a report, the reports are model-written and cut off, and 39 of the 69 insertions go into one report | **Stated in Part 1b** |
| 2 | The "0% to 5%" intervals treat the criteria as independent. They come from 10 tasks; counted by task the upper bound is about 28% | **Stated in Part 1b.** The write-up's count of criteria that mention a tolerance is also made exact: 190 contain "within +/-" and 17 the sign "±" |
| 3 | The write-up said the script was changed once after calls began. It was changed twice | **Corrected** in Part 1b and in the script's comment |
| 4 | The run was counted after each batch, closed before its cap, and reopened with results in view | **Stated in Part 1b**, with the dates |
| 5 | The records cannot prove several things: they carry no time, no served-model identifier and no prompt text | **Stated in Part 1b** |
| 6 | Spending is the script's own meter, not the provider's bill | **Stated in Part 1b** |
| 7 | The repeats show stability on the same sentences, not new evidence about criteria; some repeated replies are identical in text | **Stated in Part 1b** |
| 8 | The side-by-side table is not like for like, and "a property of the third judge, not of rubric judges in general" is more than two judges support | **Corrected.** The sentence is replaced, and the table now says how the two columns differ |
| 9 | Smaller points: the preregistration's "contracts file sha256" is the file's own receipt hash and not the hash of the file; sixteen just-outside sentences are finer than their reference; two criteria give a percent tolerance on a percentage | **Left as they are**, and said here. The test sentences are byte for byte the ones fixed before the run |

## The report, as returned

# Independent recount of the run on the second judge (DRACO, [the judge's model id])

**Outcome.** My recount from `judge_calls.jsonl` gives the same counts as the counted files: 703 records, 6 failed, 697 with a verdict, 0 wrong verdicts at any distance, in any stage, on any call. No finding below changes a count. The findings are about what is said around the counts, and about what the record cannot prove.

I changed nothing in the repository, made no network or model call, and wrote only in a scratch folder. While I worked, HEAD moved from `a41d142` to `d7f58fb`; the call record is byte-identical at `630346f`, at `d7f58fb` and on disk.

## Findings, most important first

**1. The in-report result (0 of 69) is weaker evidence than the single-sentence result.**
- This run has no in-report case whose right verdict is MET. All 69 right verdicts are UNMET, so the count alone cannot separate "did the comparison" from "refused".
- What argues against plain refusal: I read all 69 explanations, and each quotes the inserted value and the correct range.
- The "long reports" are 10 model-written texts (`results/draco_contracts/reports.jsonl`, written by [a model]), 950 to 2,196 words. All 10 have stop reason `max_tokens`, so every one is cut off.
- The 69 insertions go into 9 reports, and 39 of them into one.
- In 3 replies (lines 315, 367, 371) the judge notes that the report already carries a different figure for the same quantity.
- 30 of the 69 replies are wrapped in a json code fence, against the prompt's "no back-ticks". The script's pattern reads them, and so does my JSON parse after removing the fence. A harness that parses the raw reply as JSON would have failed on 43% of this stage. No single-sentence reply is fenced.

**2. The "0% to 5%" intervals treat the criteria as independent, and they are not.**
- From the `cluster` column: 39 of 76 criteria come from one task, then 13, 9, 4, 3, 3, 2, 1, 1, 1.
- Against the dataset: 73 of 76 are Finance, in 8 tasks.
- At task level the result is 0 of 10 tasks (0 of 9 in report). A 95% upper bound on that is about 28% to 30%, not 5%.
- The 76 are 1.9% of the rubric's 3,934 criteria. By my pattern, 190 criteria contain "within +/-"; the product's scan says 207.

**3. Report Part 1b says the script was changed once after calls began. Git shows two changes.**
- `93e05cd` (20 Nov 18:21:03): pacing at 2.7 s, 7 attempts instead of 5, and a different rule for when a refusal stops the run. This came after the first 25 records.
- `607e165` (20 Nov 18:51:08): stop at once on a per-day 429. This came after 247 records.
- Neither diff touches the stages, settings, prompts, verdict pattern or cap. `draco_contracts.py` last changed at 16:11, before the preregistration.
- The comment in the script also mentions only the first change.

**4. The run was closed and then reopened with results in view, and it was counted after every batch.**
- `7b7ba48`, `7944042` and `d8b2c69` each counted the record before the next batch ran. The commit messages' "before any counting" is true per batch, not for the run.
- `d8b2c69` (21 Nov 16:37) closed the run at 489 verdicts and 3.08 US dollars, with "final numbers" pushed. The preregistered stop is the cap only, so this was a departure.
- `810ea4f` (21 Nov 17:18) records the decision to reopen, after another experiment had been run in between. Part 1b says "reopened on 22 Nov"; the decision is dated 21 Nov and the calls were made on 22 Nov.
- Every result seen at each decision was "all right", so the decisions cannot have selected an outcome, and resuming returned the run to its plan.
- The preregistration does not say failed calls would be made again. All 6 were, and all 6 were provider refusals with no model output.

**5. The record cannot prove several things the write-up states.**
- **No timestamps.** "Before any call of the run" and the days of the calls rest on commit times alone. They are consistent: `pings.jsonl` was last written at 18:15:45, the preregistration was committed at 18:16:29 and pushed at 18:16:32, and the first 233 records were committed at 18:30:11. Pacing puts the start of the second invocation no later than about 18:20:40.
- **No served-model id.** Only the requested name is stored, it is a preview alias, and the calls span three dates.
- **The prompt sent is not stored.** I rebuilt it from the paper's TeX and the dataset. Recorded prompt tokens track its length (r = 0.997, about 4.3 characters per token), and repeated calls on one sentence have identical prompt tokens in all 152 cases. That is plausibility, not proof.
- **`judge_run.log` ends at the second batch** (21 Nov 08:24). The last 225 records, and the stop at the cap, have no log line.

**6. Spend is the script's meter and cannot be reconciled with the provider's bill from here.**
- The sum of `cost_usd` is 4.257786, and recomputing from token usage at 2 and 12 US dollars per million gives the same on every record.
- The provider returned "prepayment credits are depleted" (HTTP 402) when the meter read 1.2331, or 1.244 with the pings. Either credit was added in parts or the meter under-reads; the record cannot say which.
- The third invocation was killed (it has no closing log line), so a call in flight then would be billed without a record.

**7. The repeats add stability on the same sentences, not new evidence about criteria.**
- At −1.1: 66 criteria have two calls with a verdict, 10 have three, none has one (162 calls). At +1.1 the numbers are identical.
- No criterion's calls disagree on either side.
- Of 192 same-sentence pairs, 45 have byte-identical reply text: 25 of 96 at −1.1 and 20 of 96 at +1.1.
- Of those 45, 30 differ in thinking-token count, so they were separate generations. The other 15 cannot be told apart from a cached reply.
- No criterion with three calls has three identical replies.
- First calls were made on 20 Nov and every repeat on 22 Nov, in one batch.
- The third calls cover the first 10 criteria by id, 7 of them from the largest task.

**8. The side-by-side table is not like for like.**
- I recounted the third judge's figures from its own records and they match: 22, 10, 27 either, 14 of 69, and 6 and 5.
- Those are "wrong on any of 3 calls" at temperature 0 with reasoning off. On first calls only they are 22, 9 and 26.
- This judge had 2 or 3 calls, at temperature 0.2, with reasoning on: thinking tokens are above zero on all 697 calls, minimum 42.
- So the two columns differ in model, provider, reasoning and temperature. "A property of the third judge, not of rubric judges in general" is more than two judges support. Part 1c already says this judge was never run without reasoning.

**9. Smaller points.**
- **Contracts hash.** The preregistration's "contracts file sha256 `6c8d25012b88…`" is the file's internal receipt hash. `sha256sum` of the file at that commit gives `88b451f4…`. The file was regenerated three times afterwards (internal hash now `f446bc00…`), with labels and metadata changed and 76 items throughout. `probes.csv` is byte-identical to the preregistered one (`147522f4…`), so the cases did not change.
- **Rounding.** 16 just-outside sentences on 8 criteria state a value finer than the reference (for example "$102.5" against $97 ± $5). Rounded toward the reference they would fall inside. The right verdict assumes no rounding; the judge said UNMET on all.
- **Percent tolerances.** Two criteria say "within +/- 0.1%" on a percent value. Read as relative, the ±0.9 sentences would be UNMET. The probes and the judge both read it as points.
- **Daily limit.** Error text is stored cut at 400 characters, so the figure of 250 requests a day is not in the record.
- **In-report set.** The 7 criteria left out are those without `report_near_outside` in `items_replication.json`.

## My counts

| Stage | Distance | Context | Records | Failed | With verdict | MET | UNMET | Right | Criteria | Wrong on ≥1 call | Wrong on every call |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | −1.1 | sentence | 77 | 1 | 76 | 0 | 76 | UNMET | 76 | 0 | 0 |
| 1 | +1.1 | sentence | 76 | 0 | 76 | 0 | 76 | UNMET | 76 | 0 | 0 |
| 2 | 0 | sentence | 77 | 1 | 76 | 76 | 0 | MET | 76 | 0 | 0 |
| 2 | far | sentence | 78 | 2 | 76 | 0 | 76 | UNMET | 76 | 0 | 0 |
| 3 | +1.1 | report | 69 | 0 | 69 | 0 | 69 | UNMET | 69 | 0 | 0 |
| 4 | −0.9 | sentence | 78 | 2 | 76 | 76 | 0 | MET | 76 | 0 | 0 |
| 4 | +0.9 | sentence | 76 | 0 | 76 | 76 | 0 | MET | 76 | 0 | 0 |
| 5 | −1.1 | sentence | 86 | 0 | 86 | 0 | 86 | UNMET | 76 | 0 | 0 |
| 5 | +1.1 | sentence | 86 | 0 | 86 | 0 | 86 | UNMET | 76 | 0 | 0 |
| All | | | 703 | 6 | 697 | 228 | 469 | | | 0 | 0 |

- **Complete stages.** Stages 1 to 4 have every planned (probe, context, call) with exactly one verdict: 152, 152, 69, 152.
- **Stage 5.** 172 of 304: all 152 second calls and 20 of 152 third calls, a contiguous prefix of the plan. The next planned call was `354c41550164@-1.1`, call 2.
- **Duplicates.** No key has two verdict records. Six keys have two records, one failed and one with a verdict.

**Verdict reading.** My reading differs from the stored `verdict` on 0 replies. None is cut off (every `finish_reason` is `stop`; the largest output plus thinking is 761 of 2,048 tokens), none is empty, and `criterion_status` appears exactly once in each.

**Failed calls.** Each has a later verdict on the same key.

| Line | Stage | Probe | Refusal | Verdict at line |
|---|---|---|---|---|
| 22 | 1 | `393e0b478c86@-1.1` | 429, per-minute request limit of 25 | 26 |
| 232 | 2 | `806277bd8698@far` | 402, prepaid credit depleted | 238 |
| 233 | 2 | `7d39b032c4de@far` | 402, prepaid credit depleted | 234 |
| 251 | 2 | `90fcbfd65765@0` | 429, per-day request limit | 253 |
| 477 | 4 | `9875f6e03600@-0.9` | 429, per-day request limit | 479 |
| 494 | 4 | `ba7b9f3b1eec@-0.9` | 429, per-day request limit | 496 |

**Rules.**

| Rule | My count | Outcome |
|---|---|---|
| G1 | 0 of 76 accepted at −1.1 | Not shown |
| G2 | 0 of 76 accepted at +1.1 | Not shown |
| G3 | 0 of 76 wrong on the exact value, 0 of 76 on far off | Harness not suspect by the rule |
| G4 | 0 of 69 accepted in report | Not shown |
| G5 | 0 of 76 refused at −0.9, 0 of 76 at +0.9 | Reported as counted |
| G6 | Stage 5 incomplete at 172 of 304; no disagreement on any of 76 criteria, either side | Agree, as far as it got |
| G7 | No verdict on 1 of 153, 3 of 155, 0 of 69, 2 of 154, 0 of 172 records | No stage above 5% |

G7 does not say whether its denominator is records or planned calls. With planned calls, stages 1 to 4 are at 0%, and stage 5 has 132 of 304 never made. That is "incomplete" under the stopping rule, not "unreliable".

**Spend.** The meter read 4.244642 after line 701, below the cap. Line 702 took it to 4.251292, and line 703, already in flight, to 4.257786. The run ended 0.007786 over the cap, which fits two workers. The two pings add 0.010806 and are outside the cap, for 4.268592 in all.

**Commits touching the call record.** Each version starts with the previous one, line for line; nothing was changed or removed. Local push records show each pushed within seconds, with no forced update.

| Commit | Time (UTC) | Records added | Total |
|---|---|---|---|
| `5368e8e` | 20 Nov 18:30:11 | 233 | 233 |
| `607e165` | 20 Nov 18:51:08 | 14 | 247 |
| `cc1b115` | 21 Nov 07:17:39 | 5 | 252 |
| `fdeeccd` | 21 Nov 08:24:58 | 226 | 478 |
| `706f6a2` | 21 Nov 16:35:07 | 17 | 495 |
| `630346f` | 22 Nov 09:11:18 | 208 | 703 |

By commit date, the records fall as follows:

| Date | Records | Stages |
|---|---|---|
| 20 Nov | 247 | Stage 1, and 94 records of stage 2 |
| 21 Nov | 248 | 61 of stage 2, stage 3, and 118 of stage 4 |
| 22 Nov | 208 | 36 of stage 4 (the last 18 criteria), and stage 5 |

## Checked and found correct

- **Right verdicts.** I parsed the reference and tolerance from each criterion's text and the stated value from each sentence, in exact decimals. All 456 probes used agree with `probes.csv` on stated value, reference, tolerance and verdict. Every ±0.9 and ±1.1 sentence is exactly that distance; far-off ones are 4 to 381 tolerances out.
- **Criteria.** All 76 appear verbatim in the dataset's rubric for their task, each once, all with positive weight.
- **Order.** Stage numbers never go down in file order and each stage is one contiguous block. 24 records are out of strict plan order, by at most 4 positions.
- **Settings and model.** Identical on all 703 records and both pings (`temperature` 0.2, `reasoning_effort` low, `max_tokens` 2048); one requested model name. The paper's table gives thinking level low and temperature 0.2 for its primary judge.
- **Text hashes.** All 634 single-sentence records match the sha256 of the probe's `response`. All 69 in-report records match `items_replication.json`, and also match the text I rebuilt from the stored report and the probe sentence.
- **Same text as the earlier judge.** Every text in every stage has the same hash as one sent to the third judge for that criterion.
- **Counted files.** `verdicts.csv` and `table.csv` hold exactly the 697 verdict records. Run on my own verdict reading, the tool rebuilds `table.csv` byte for byte. `grader_check.txt` and `grader_receipt.json` equal my counts in every group. `verify` passes on the grader receipt and on the probes receipt. `run_summary.json` matches on calls, stages, spend and tokens.
- **Stopping points.** Cumulative spend at each batch boundary matches the log and commit messages: 0.1402, 1.2331, 1.3002, 1.3195, 2.9994, 3.081, 4.2578.
- **Grading prompt.** The text extracted from the TeX is 5,173 characters with no TeX commands in it.

## Not checked

- Anything at the provider: the bill, the daily limit's figure, whether the paper's primary judge is withdrawn, whether this model is its direct successor, how `reasoning_effort` maps to the thinking level, and which model version served each call.
- The exact prompt bytes sent, and whether `<query>…</query>` is how the benchmark's own library wraps the query.
- The product's scan (that 76 is the complete set of checkable criteria); `verify` on the contracts file needs the rubric file and I did not re-run it.
- The code of `consilience-judge-check`; I checked only that its output equals my count.
- The earlier arms beyond the five side-by-side figures, Part 1c, the cost of the whole study, and any write-up other than Part 1b.
- Server-side push times on the remote.
