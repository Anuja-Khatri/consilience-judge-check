# Independent audit of the DRACO judge study, and what was done about it

20 Nov 2026. Before this study was shown to anyone, its main figure was checked two ways: a preregistered replication (`PREREGISTRATION_DRACO_REPLICATION.md`) and this audit.

**Who audited.** A separate AI session that did not write the study. It was given the code, the call records, the dataset, the paper source and the two write-ups, and was told to try to break the numbers. It was not given the study's conclusions as facts. It made no model calls. It ran while the replication arm was being made and did not audit that arm.

**What it is not.** It is not a human review, and the auditor is the same kind of system as the author. It caught real errors, which is evidence it was not a rubber stamp, but a person who works on DRACO would know things neither session does.

## What was done about each finding

| # | Finding | Checked by me | What changed |
|---|---|---|---|
| 1 | "The judge was right" on the three items it called MET on the report alone is true for one of three. In one the judge quoted a sentence that is not in the report. In one it accepted "~$23M" for $23,140k ± $100k | Yes, against the report text: confirmed | The sentence is corrected in both write-ups. The two are reported as further judge errors, outside the counted set. The rows stay left out of the engine's table under the original rule (the judge called the report alone MET), now with the true reason |
| 2 | The 95% intervals treated 228 calls as independent. They are 76 criteria called three times at a near-deterministic setting, from 10 tasks, one of which holds 39 criteria | Yes: confirmed | Every table now counts criteria, with criterion-level intervals, counts by task, the rate without the largest task, and an interval from resampling tasks (`pilot/draco_robustness.py`) |
| 3 | "The errors sit near the edge" and "away from the edge the judge is right" overstate: 15 of the first 80 errors are at 0.5 or 2 tolerances | Yes | Reworded with the counts at each distance |
| 4 | Three "made no difference" sentences hold only in total: another unit, a long report, a note to the grader | Yes | Each now says which criteria changed |
| 5 | "Decides exactly" was not what the engine did: floating point with a guard of one part in a billion. A value 50 dollars past the edge of a half-billion tolerance was called inside. No DRACO row was affected. 33 table rows carried float noise in the reference | Yes: reproduced | The engine now decides same-unit rows in exact decimal arithmetic and leaves a cross-unit value at the edge undecided. Two tests added from the auditor's case. Tables rebuilt in exact decimals from the criterion's own digits. Receipts regenerated; counts unchanged |
| 5b | The table's numbers come from the study's own script and every row has one unit, so "the engine found the same 80" is expected by construction | Agreed | Said plainly in both write-ups |
| 6 | Some near-edge values are less than one displayed digit past the edge, and the example quoted first ($66.2M against $62M to $66M) rounds onto the edge | Yes | A rounding check was added: how many accepted values are still outside after rounding toward the reference at the criterion's own precision. The lead example was replaced with one written at the criterion's own precision. The caveat about extra decimal places is in both write-ups |
| 7 | Small mismatches: three interval limits rounded twice; 216 against 207 for the in-report rows; "207 criteria state a tolerance" counts one wording only; "3% to 71%" is all tolerance criteria, not the 76 tested | Yes. My recount of any plus-or-minus sign gives 215 in 24 tasks (the auditor's 212 used a narrower pattern) | Corrected |
| 8 | Seven calls scored right have an explanation that says the opposite of the status | Partly: a rule finds 3 of them among counted calls; the auditor read by hand | Reported. The status field is what DRACO scores and what was counted |
| 9 | The harness is not DRACO's: an output limit the paper does not state, the judge wrapping its reply in a code fence against the prompt's instruction, the query wrapper | Agreed | Listed under limits |
| 10 | Parsing: all 76 match. Two criteria ("5.31% (within +/- 0.1%)") could be read as relative; the judge read them as absolute every time | Not re-checked | Noted |

**Checked by the auditor and found sound:** 552 responses recomputed from their text with exact decimals (0 wrong labels, 0 on the boundary); the item files rebuild identically; all four preregistration hashes match; all 2,388 response hashes match; verdict parsing (0 mismatches, 0 nulls, 0 cut off); every per-condition count; 2,298 engine rows against independent decimal arithmetic (0 differences). Of the 80 wrong verdicts it classed 77 as contradicting the judge's own reply, 3 as unit slips, 0 as a defensible reading of the criterion.

## The auditor's report, as returned

The text below is the auditor's, unedited.

---

# Audit of the DRACO judge study: findings

The headline counts all reproduce (80 wrong of 2,316 known-answer calls; 2,298 / 2,218 / 57 / 23). What does not hold is one factual sentence, the intervals, and several "made no difference" sentences.

## Findings, most serious first

**1. CONFIRMED. "The judge was right" on the three report-alone MET items is true for one of three.** (Report item 9 and the "2,298 and not 2,388" bullet.)
- `0a8a11cb9589`: the report says "approximately $10 million principal". The judge was right.
- `6097b4a4aac0`: the judge quotes "As of September 30, 2025, unsecured term loans stood at approximately $1,100 million". That sentence is not in the report: no "1,100", no "unsecured term loans", no "stood at". The quote is fabricated.
- `6ac122ee5d82`: the report says "~$23M"; the criterion is $23,140k ± $100k. The judge wrote "falls within ($23,040k to $23,240k)", which is a lenient error.
- **Change:** rewrite the sentence; these are two further judge errors, uncounted. "The report already stated the figure" is false for `6097b4a4aac0`. Restoring its six in-report rows gives 2,304 / 2,224 / 57 / 23 and README in-report rows of 0 of 210 and 5 of 210. The 80 does not change.

**2. CONFIRMED. The 95% intervals are too narrow.**
- They treat 228 calls as independent. They are 76 criteria × 3 near-identical repeats: 523 of 772 reply triples are byte-identical, and 9 split on verdict.
- The criteria come from 10 tasks. One task holds 39 of 76 criteria and three hold 61.
- Wrong calls come from 23 criteria in 7 tasks. Just outside, the big task fails on 1 of 39 criteria and the other nine on 9 of 37.
- **Change:** replace the interval column in both write-ups with criterion-level intervals and state the task clustering.

| Condition | Quoted (by call) | By criterion | 95%, criteria independent | 95%, resampling tasks |
|---|---|---|---|---|
| Just outside, 1.1 T | 11.4% (7.9 to 16.2) | 10 of 76 = 13.2% | 7.3 to 22.6 | about 5 to 31 |
| Just inside, 0.9 T | 5.3% (3.0 to 9.0) | 5 of 76 = 6.6% | 2.8 to 14.5 | 0 to 10 |
| Other unit, outside | 15.3% (10.3 to 22.1) | 8 of 48 = 16.7% | 8.7 to 29.6 | about 4 to 44 |
| Exact, far | 0% (0 to 1.7) | 0 of 76 | 0 to 4.8 | n/a |

**3. CONFIRMED. "The 80 errors sit near the edge" (README) and "Away from the edge … the judge is right" (Report item 1) overstate.**
- 65 of the 80 errors are at 0.9 T or 1.1 T. The other 15 are at 0.5 T or 2 T (15 of 1,116 calls), including "$50,000 … within ($35,000 to $45,000)".
- **Supportable:** "0 of 456 at the exact value and at 4 T or more; 15 of 1,116 at 0.5 T and 2 T; 65 of 744 at 0.9 T and 1.1 T."

**4. CONFIRMED. Three "no difference" sentences hold only in aggregate.**
- **Other unit:** 22 of 144 both ways, but only 4 of the 8 failing criteria are the same. The unit change flipped the verdict on 8 of 48 criteria. Just inside is 3 against 5.
- **Long report "changed little":** the comparison mixes criterion sets. On the 72 criteria tested both ways, inside goes from 6 of 216 bare to 0 of 216 in a report, and outside from 0 of 216 to 5 of 216 (Fisher p = 0.06). Different criteria fail.
- **Note "did nothing":** without it `3ca4599feecd` is wrong 3 of 3; with it that item is right 3 of 3 and `fdd2e5eb0705` is wrong 1 of 3.

**5. CONFIRMED. "Decides exactly" (README lines 3 and 52) is not what the engine does.**
- `compare` uses floats with a guard of 1e-9 × value. My synthetic row (reference $65.6B, tolerance $0.5B, stated $66,100,000,050) is called met, and a grader that rejects it is labelled "strict".
- No DRACO row is affected: the closest is 1.3e-4 (relative) from the edge.
- 33 table rows carry the reference `65599999999.999992` for $65.6B (float noise from the script).
- Every row has the same unit on both sides, and all three numbers come from the study's own script. So "the engine decided" means one inequality, and "the same 80, row for row" is expected by construction.

**6. CONFIRMED. Some near-edge cases are arguable by rounding, and the lead quote is the weakest.**
- "$66.2M … ($62M to $66M)" (`21c6094c2376`) rounds onto the edge at the criterion's own precision ("$64M"). It accounts for 6 wrong calls.
- 27 of the 48 "just outside" wrong calls are on values less than one last-displayed digit past the edge.
- The second preregistration's caveat ("more decimal places than a real report would") is missing from both write-ups.
- **Change:** lead with `6097b4a4aac0` or `3ca4599feecd`. Without `21c6094c2376` the counts are 23 of 228, 19 of 144, 74 total, 51 lenient.

**7. CONFIRMED. Small number mismatches.**
- Wilson limits double-rounded: "0.5 to 3.8%" should be 0.4; "10.3 to 22.1%" should be 22.0; the Report's "0 of 216 … 1.8%" should be 1.7.
- The Report uses 216 for the in-report rows and the README uses 207 (2.3% against 2.4%), unexplained.
- "207 criteria state a tolerance" counts only the "within +/-" wording. Five more use "(+/- £0.01m)", giving 212 in 24 tasks.
- "3% to 71%" covers all tolerance criteria in the ten tasks. The 76 tested carry 2.5% to 59%.

**8. CONFIRMED. Seven calls scored "right" have explanations that say the opposite of the status.**
- All are in-report outside calls with status UNMET and text such as "falls within … The criterion is satisfied": `0a8a11cb9589` ×3, `6ac122ee5d82` ×2, `7d39b032c4de` rep 1, `b8e87ef67d40` rep 2.
- Two of them sit inside the 2,218. The judge's explanation is not a reliable account of its verdict.

**9. Prompt fidelity.** The system prompt is byte-identical to the TeX listing. Differences:
- `{query_text}` is sent as `<query>…</query>`; the claim that this follows the open library is unverifiable offline.
- `max_tokens` is 1024; the paper states none. The longest reply is 226 tokens and none was cut off.
- Temperature 0 is sent via `extra_body` and not echoed in the records.
- SUSPECTED: all 2,388 replies are wrapped in a json code fence despite "no back-ticks". If DRACO's harness forces raw JSON, a few verdicts could differ.

**10. Parsing.** All 76 match my independent parse and `test.jsonl` verbatim. The only alternative reading is on `00c8dc0cd995` and `ba7b9f3b1eec` ("5.31% (within +/- 0.1%)" could be relative). The judge used the absolute reading every time, so no count changes.

## Are the wrong calls really wrong?

| Condition | Wrong | (a) contradicts own reply | (b) defensible reading | (c) other |
|---|---|---|---|---|
| Inside, 0.5 T | 6 | 6 | 0 | 0 |
| Just inside | 12 | 12 | 0 | 0 |
| Just outside | 26 | 25 | 0 | 1 |
| Outside, 2 T | 3 | 3 | 0 | 0 |
| Other unit, inside | 5 | 5 | 0 | 0 |
| Other unit, outside | 22 | 20 | 0 | 2 |
| In report, outside | 5 | 5 | 0 | 0 |
| With note | 1 | 1 | 0 | 0 |
| **Total** | **80** | **77** | **0** | **3** |

- The three in (c) are unit slips: `7d39b032c4de` ("within $55 … of +/- $50k") and `2c86fbbf812c` ×2 ("within $110 … +/- $100k"). The judge dropped "thousand".
- Every range the judge wrote out was the correct one.
- "A mis-comparison, not a misreading" holds for 77 of 80.

## Checked and found sound

- **Responses:** 552 recomputed from the sentence text with exact decimals: 0 wrong expected verdicts and 0 on the boundary. All sit at 0, 0.5, 0.9, 1.1 or 2 T, or at least 4 T away.
- **Rounding:** rounding to the criterion's precision reaches the edge for 1 item (half-up), 3 (half-even) or 8 (truncation).
- **Garbling:** no sentence changes meaning. There are five verbless fragments and odd forms such as "$1,969.5k" and "$191.603 thousand".
- **Reproducibility:** `items.json` and `items_boundary.json` rebuild identically from the script, and all four preregistered hashes match.
- **What was sent:** all 2,388 response hashes match the stored texts.
- **Verdict parsing:** 0 mismatches, 0 nulls, 0 cut off, 0 with two statuses.
- **Counts:** every per-condition count, the at-least-once and every-call counts, 15 of 1,572, the family split, 22 and 22 of 144, and the 72 + 18 exclusions all match.
- **Engine:** 2,298 rows against my decimal arithmetic give 0 differences, and `verify` passes.

While I worked, another process added `draco_replication.py` and related files to both trees; they are not mine and I did not audit them.
