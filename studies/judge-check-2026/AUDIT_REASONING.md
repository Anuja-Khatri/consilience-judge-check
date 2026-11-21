# The independent recount of the reasoning experiment

On 21 Nov 2026 the paper's third judge was run again on the just-outside sentences, with its reasoning switched on and with a control (Part 1c of the write-up). Before the result was written up, a separate AI session, which had not run the experiment, was given the call records and the code, not the conclusion, and asked to recount.

- **It reproduced every count.**
- **It listed twelve things that limit the claim.** The three that matter most are now stated first in Part 1c.
- **It was done by an AI session, not by a person.**

Its report is below as it was returned. Two kinds of words are replaced, and nothing else is changed: the path of its scratch folder, and the judge's model identifier, written `[the judge's model id]`.

## What was done about each finding

| # | Finding | What was done |
|---|---|---|
| 1 | With reasoning on, only sentences whose right verdict is UNMET were tested. A judge that refused everything would score the same | **Stated first in Part 1c.** The write-up says "stops accepting values just outside", not "accurate". Not run: values inside the tolerance with reasoning on |
| 2 | "Reasoning on" is more than one change: the reply limit was larger, and the provider adds about 30 tokens to the prompt that the records do not show. The script's comment and the preregistration's table left out the reply limit | **Stated in Part 1c.** The comment in the script is corrected. The preregistration is left as written |
| 3 | The side above the reference has no control, and its rule sits on the threshold | **Stated in Part 1c.** It was declared in advance |
| 4 | "Removed" is not zero: one new error | **Stated in Part 1c**, with the judge's own words |
| 5 | The control against the paper's settings is a weak comparison | **Stated in Part 1c**: it shows the change of temperature does not remove the error, not that temperature has no effect |
| 6 | The preregistration said a "yes" would explain why the two judges differ. The run does not test that | **Stated in Part 1c.** The write-up says the result fits that explanation and does not prove it. The preregistration is left as written |
| 7 | The 76 criteria are effectively 10 tasks | **Stated in Part 1c**, with the count by task |
| 8 | Eight sentences on each side are arguable for a reader who rounds | **Stated in Part 1c**, with the counts without them |
| 9 | Reply format differs between settings | **Stated in Part 1c.** It does not change any verdict read |
| 10 | Order of events holds. The two trial calls were made with the script before its list of stages was shortened | **Stated in Part 1c** |
| 11 | The cost adds up | Nothing to do |
| 12 | Two flaws in the script that this run did not trigger: failed calls would be left out of the verdict files, and the spending cap does not count the trial calls | **Left as run**, and said here. No call failed, and the run ended under its cap with the trial calls counted in |

## The report, as returned

# Independent check of the DRACO reasoning experiment

**The counts reproduce exactly: 0 of 76, 24 of 76 and 1 of 76 criteria accepted, with no failed or unreadable call.** By the preregistered rules that is R1 "Removed", R2 "Not removed", R3 "Removed", and the first row of the table: "The reasoning step removes the error". I found no counting error, no missing or duplicated record, and no mismatch between the stored verdicts and my own reading of the replies.

What follows is what limits the claim, ranked by how much it matters.

## Findings

1. **Only sentences whose right verdict is UNMET were put to the judge with reasoning on.**
   - A judge that rejected everything would score the same 0 of 76.
   - The texts argue against that: in 151 of 152 calls the reasoning or reply does the correct arithmetic. 146 write the violated bound; 5 compute the difference and compare it with the tolerance.
   - No sentence inside the tolerance (0, -0.9, +0.9) was run with reasoning on. The result supports "stops accepting values just outside", not "accurate with reasoning on".

2. **"Reasoning on" is more than one change.** What is sent, from the two scripts:

   | | Paper settings (earlier) | `reasoning_on` | Control |
   |---|---|---|---|
   | Model | [the judge's model id] | same | same |
   | System prompt | read from the paper's TeX at run time | same function | same function |
   | User prompt | criterion, "positive", task text, sentence | same | same |
   | Temperature | 0 | not sent | not sent |
   | Reasoning | not sent | enabled, budget 1,024 | not sent |
   | Max tokens | 1,024 | 2,048 | 1,024 |
   | API version header | 2023-06-01 | same | same |
   | Calls per sentence | 3 | 1 | 1 |
   | Date | 20 Nov | 21 Nov | 21 Nov |
   | Input tokens per call | N | N + 30 | N |

   - The control differs from the paper arm in what is sent only by temperature. Input tokens are identical on all 76 sentences.
   - `reasoning_on` differs from the control by the reasoning setting, max tokens, and exactly 30 extra input tokens on every one of its 152 calls. The records do not show what those tokens are.
   - 19 of 152 reasoning-on replies begin with a stray `<budget:…>` tag; none of the 76 control replies and none of the 456 earlier ones do. Together with the extra tokens, this suggests the provider adds something to the prompt when reasoning is on.
   - The script comment "Nothing else differs between the arms" is wrong about max tokens, and the preregistration's table omits it. It did not bind: the largest reply was 492 output tokens and every call ended normally.

3. **The side above the reference has no control.** R3 compares reasoning on (21 Nov, default temperature) with the paper arm (20 Nov, temperature 0). The preregistration declared this.
   - All 9 first-call errors of the paper arm went, and 1 new one appeared (exact paired p = 0.02, treating criteria as independent).
   - R3 sits on its threshold: 1 accepted is "Removed", 2 would have been "Reduced".

4. **"Removed" is not zero.**
   - The one acceptance is `ed5343d2fceb@+1.1`: "$102.5" against "$97 (within +/- $5)". The judge writes the range as $92 to $102 and then says $102.5 is within it.
   - The paper arm rejected this sentence on all three calls, so it is newly wrong.
   - With one call per sentence: 1 wrong in 152 calls (95% interval up to 3.6%); at 1.1 below alone, 0 of 76 (up to 4.7%).

5. **The control against the paper arm is a weak comparison.**
   - 24 against 22 of 76: 19 the same, 5 new, 3 gone (exact p = 0.73).
   - The difference is +2.6 points, with an interval of about -4.6 to +9.9.
   - It shows temperature alone does not remove the error. It does not show temperature has no effect.
   - The two arms also differ in date and in one call against the first of three.

6. **The preregistration's inference about the two judges is not tested.** The run shows reasoning is sufficient for this judge on these sentences. It does not show reasoning is why the other judge is right: that judge was never run without reasoning, and it differs in model, provider and temperature (0.2).

7. **The 76 criteria are effectively 10 tasks.**
   - Task sizes are 39, 13, 9, 4, 3, 3, 2, 1, 1, 1; 8 of the 10 are Finance; 58 criteria are in US dollars.
   - The control's 24 acceptances fall in 7 tasks (14 in the largest); reasoning on has none in any task. A sign test by task gives 7 against 0, p = 0.016.
   - The largest task does not drive it: outside it, 10 of 37 against 0 of 37.
   - Three tasks (7 criteria) had no error in any arm.

8. **Eight probes on each side are arguable for a reader who rounds.**
   - All 152 are outside by exact arithmetic, at exactly 1.1 tolerances.
   - 11 per side state the value more finely than the reference; for 8 of them, rounding toward the reference lands inside the tolerance.
   - 5 of the control's 24 acceptances and the single reasoning-on acceptance are among these.
   - Without them, at 1.1 below: control 19 of 68, reasoning on 0 of 68. The outcome does not change.

9. **Reply format.**
   - With reasoning off, every reply is wrapped in a code fence despite the prompt's "no back-ticks".
   - With reasoning on, 100 of 152 are bare JSON, 33 fenced, 19 start with the stray tag.
   - None of this changes the verdict read: every reply holds the status field exactly once and parses as complete JSON with two keys. A reader that required raw JSON would reject 52 of the 152.

10. **Order of events holds, on local clocks.**

    | Time (21 Nov, UTC) | Event |
    |---|---|
    | 17:10:56 | Pings written |
    | 17:11:41 | Preregistration and script committed (`c43b37a`) |
    | 17:11:43 | That commit pushed |
    | 17:11:52 | Call record created |
    | 17:15:47 | Call record last written |
    | 17:15:56 | Call record committed (`2db4fcf`) |
    | 17:15:58 | First counted file created |
    | 17:17:55 | Counted files committed (`f834045`), while I was working |

    - The preregistration and script on disk are byte-identical to the committed ones; the call record on disk is identical to `2db4fcf`.
    - The record's lifetime (235 s) matches the sum of call times over 4 workers (236 s), so there is no sign of a restart or a removed run.
    - The script was last modified at the instant the preregistration was created, after the pings. The pings were therefore made by an earlier version that is not recorded; their recorded settings equal the committed ones.

11. **Cost adds up.** 364,810 input and 47,824 output tokens give 1.0944 + 0.7174 = 1.8118 US dollars, which matches `run_summary.json`. The pings add 0.0187, for 1.8305 in total. Per call: 0.0088 and 0.0090 with reasoning on (preregistered 0.0094), 0.0061 for the control.

12. **Two latent flaws in the script, neither triggered.** `verdicts()` silently leaves failed calls out of the verdict files, which would shrink the denominator; the spending cap does not count the pings.

## My counts

| Arm | Distance | Calls | Failed or unreadable | Criteria accepted |
|---|---|---|---|---|
| `reasoning_on` | 1.1 below | 76 | 0 | 0 of 76 |
| `reasoning_off_default_temperature` | 1.1 below | 76 | 0 | 24 of 76 |
| `reasoning_on` | 1.1 above | 76 | 0 | 1 of 76 |
| Paper settings, first call | 1.1 below | 76 | 0 | 22 of 76 (22 at least once in three) |
| Paper settings, first call | 1.1 above | 76 | 0 | 9 of 76 (10 at least once in three) |

- **Paper arm's errors at 1.1 below (22):** reasoning on gets all 22 right; the control gets 3 right.
- **Newly wrong at 1.1 below:** 5 for the control, none for reasoning on.
- **Still wrong, control:** 22 of its 24 acceptances write out the correct range and still say MET.

## Checked and found correct

- **Verdict reading.** My own JSON parse equals the stored `verdict` on 228 of 228; no reply is cut off, empty or ambiguous.
- **Right verdicts.** All 856 stored right verdicts in `probes.csv` equal my exact decimal arithmetic.
- **Same sentences.** `response_sha256` equals the hash of the probe text on all 228 new calls and on all 456 earlier calls at these distances.
- **Same criteria.** Criterion text, task and positive weight match the earlier items file and the dataset for 76 of 76.
- **Baseline.** `table_saved.csv` equals the raw earlier records on 456 of 456, and gives 22, 22, 9 and 10; the "27 of 76" is the union of both sides.
- **The tool.** Rebuilt from my own verdict files, its tables have the same sha256 as the committed ones, its printed counts match mine, and `verify` passes on both receipts.
- **Records.** Each arm and probe appears once, one model throughout, and every reply quotes its own probe's number.
- **Pings.** Two, at 3 tolerances out, both UNMET, and neither is in the run.
- **Temperature took effect.** Control replies are byte-identical to the temperature-0 reply on 10 of 76, against 55 of 76 between two temperature-0 calls.

## Not checked

- Anything needing the network: server-side push times, actual billing, the provider's rules on temperature with reasoning and on the smallest budget.
- Which interpreter and library version made the calls, and what temperature the provider actually applied.
- The system prompt and task text as sent: they are not in the records. The evidence is indirect: same function, source files unchanged since 20 Nov 12:52, identical token counts.
- How `probes.csv` was derived from the rubric, and the tool's own code.
- All 228 replies by eye: I read them by rule and about 15 by eye.
- The other judge beyond a quick count (0 of 76 on each side in its table).

I changed nothing in the repository; `git status` is clean.
