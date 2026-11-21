# A test for rubric judges, built from the rubric alone: DRACO and DiscoverPhysics

**In one line.** Where a rubric criterion states a number and a tolerance, the right verdict is arithmetic. `consilience-judge-check`, a Consilience tool, finds those criteria in a rubric, builds test responses whose right verdict is known, and reports where a judge's verdict differs. This folder is the first study that used it, on two public benchmarks: DRACO (Perplexity) and DiscoverPhysics.

**What it offers a benchmark's authors.** A way to tell judges apart on the criteria whose answer is not a matter of judgement, with nothing to label. It runs no judge and no model: you run yours on the cases and hand back the verdicts.

```bash
consilience-judge-check scan rubric.csv --out contracts.json
```

```bash
consilience-judge-check probes contracts.json --out probes.csv
```

```bash
consilience-judge-check table probes.csv verdicts.csv --out table.csv
```

```bash
consilience-judge-check check table.csv --receipt receipt.json
```

**A note on names.** When this study was run, these commands were part of the `consilience` package and were called `consilience rubric scan`, `rubric probes`, `rubric table` and `consilience grader-check`. The preregistrations, the scripts in `pilot/` and `adapters/` and the audit records use those names and are kept as written. The code moved to this repository on 21 Nov 2026. Every receipt in this folder re-runs unchanged with the moved code.

**What the tool adds to the usual ways of checking a judge, and what a first reading might assume,** are on the front page of this repository: [README.md](../../README.md).

## What was found

| Benchmark | Question | Result |
|---|---|---|
| DRACO | Does the judge apply the tolerance a criterion states? | **It depends on the judge.** On the same 76 criteria and the same sentences, the paper's third judge accepted a value just outside the stated tolerance for 27 criteria (10 above the reference, 22 below), and the current judge of the paper's primary family accepted none, including inside a long report (0 of 69 against 14 of 69). Both judges were right on exact and far-off values |
| DiscoverPhysics | Does a wrong law pass the explanation score, and does the answer depend on which judge is used? | With the default judge, 0 of 38 wrong-law explanations reach the paper's pass mark. With a stronger judge from the same provider, 4 of 38 do, and 12 of 38 reach the public code's mark. All 5 correct explanations written in plain words fail at least once under the default judge |

Where the third DRACO judge is wrong, its own reply nearly always shows the mistake: "The response states the exam fee as $82, which falls within the acceptable range of $93 ± $10 ($83–$103)."

**For DRACO's authors, the short version.** The judge family behind the paper's main results does not show this error on these cases. The third judge, used in the paper's judge-comparison appendix, does. The test that separates them is one command per step and needs no labels.

## Read this before the numbers

- **Two judges, and neither is the paper's primary judge as published.** The third configuration in the paper's judge table (reasoning off, temperature 0) is tested in full. The paper's primary judge has been shut down by its provider, so its direct successor in the same model line was tested, at the paper's settings for the primary judge (thinking level low, temperature 0.2). The paper's second judge is not tested.
- **The run on the second judge is one call per criterion, and it was closed early.** It was stopped on 21 Nov before its spending cap, by the author's decision, when the provider's limit of 250 requests a day would have carried it into a third day. Not run: 18 of the 76 criteria just inside the tolerance, and all the repeat calls. So nothing here says whether this judge's verdicts are stable from call to call.
- **Built responses, not real system reports.** No system's reports are public, so the judge could not be re-run on them. Each response states one value in one sentence, sometimes to more decimal places than a real report would use. **Nothing here says any system's score or rank would change.**
- **76 criteria from 10 DRACO tasks, 73 of them Finance. One task holds 39 of the 76.** They are all the criteria that state a tolerance and pass the parsing rules, so the replication used new values on the same criteria.
- **This harness is not DRACO's.** The grading prompt is the paper's, byte for byte. The output limit (1,024 tokens; no reply was cut off) is this study's, and the judge wrapped every reply in a code fence although the prompt says not to. The status field was read by rule. If DRACO's own harness forces a different output form, a few verdicts could differ.
- **How the DRACO arms were ordered.** The first was written down before any call. The second (values near the edge) was designed after the first was read. The third is a replication of the second, with a pass rule fixed and committed before its calls.
- **The DiscoverPhysics numbers are small**: 38 wrong-law texts and 5 plain-words texts in five worlds, and three judges from one provider.
- **The altered values in the test items are deliberately wrong.** They are inputs for a test and state nothing about any company.
- **The reader of rubrics is narrow.** It reads criteria worded like DRACO's: they start with "States", end with "(within +/- T)", and give a dollar amount, a percentage or a count. It has not been tried on a second rubric.
- **It was audited, by other AI sessions and not by a person.** One audit found errors in the first write-up of this study (`AUDIT.md`), which are corrected. Three audits of the rubric reader each found hostile criteria it misread, and it was rewritten after each (`AUDIT_PRODUCT.md`). **The final reader has not had an audit of its own**, and another would very likely find more. For DRACO the 76 criteria it accepts were checked value by value.

## Why these two benchmarks

Both are listed under Frontier evals on Perplexity's research page, both score partly with a language-model judge, and both papers name the judge as a limit:

| Source | Words |
|---|---|
| Perplexity research page, on rewards | "rewards that are verifiable where possible and rubric-graded where not" |
| DRACO paper | "absolute scores depend on LLM judges and may not perfectly align with human expert preferences" |
| DRACO dataset card | "LLM judge variance… Results should be compared within consistent judge configurations" |
| DiscoverPhysics paper | "The explanation score relies on a single LLM judge… ideally this would be averaged over multiple judge models"; the thresholds "are also somewhat arbitrary" |

This study takes the first line literally: it finds the part of a rubric that is verifiable, and measures the judge on it.

## Credit

This check was possible only because both benchmarks publish their rubrics, prompts and code. DRACO's criteria state their tolerances explicitly, which is what makes them checkable at all. The DiscoverPhysics judge, rubrics and reference explanations are used through the benchmark's own code, unchanged. The rubric fault in the `fractional` world mentioned below was found and reported on the benchmark's repository by an outside reviewer before this study.

---

## Part 1. DRACO: does the judge apply the rubric's own tolerance?

**What was tested.** 207 of DRACO's 3,934 criteria state a number and a tolerance in the wording "(within +/- T)", for example "States … revenue as $30.8B (within +/- $0.5B)". The grading prompt tells the judge: "For numerical values: Check if they fall within specified ranges or match exactly as required." 76 of the 207 parse under strict rules into a claim, a value and a tolerance. For each, the response is the criterion's own claim with only the number changed.

**Set-up.** The grading prompt printed in the DRACO paper's appendix, unchanged, with the query wrapped as the benchmark's open grading library does. The third judge configuration in the paper's table. Three calls per single-sentence response. 3,141 calls in three arms, none failed.

**The unit is the criterion.** At this judge's setting, three calls on one response are near-identical, so they are not three trials. A criterion counts as wrong if any of its calls gave the wrong verdict. Intervals are 95% and treat criteria as independent; the section on tasks below shows what happens when they are not.

T is the criterion's stated tolerance.

| The number stated | Arm | Right verdict | Criteria judged wrongly | 95% interval | Wrong calls |
|---|---|---|---|---|---|
| The criterion's own value | First | MET | 0 of 76 | 0% to 5% | 0 of 228 |
| 0.5 T above | First | MET | 2 of 76 | 1% to 9% | 6 of 228 |
| 0.9 T above | Second | MET | 5 of 76 | 3% to 14% | 12 of 228 |
| 0.9 T below | Replication | MET | 6 of 76 | 4% to 16% | 17 of 228 |
| **1.1 T above** | Second | UNMET | **10 of 76** | 7% to 23% | 26 of 228 |
| **1.1 T below** | Replication | UNMET | **22 of 76** | 20% to 40% | 63 of 228 |
| 1.5 T above | Replication | UNMET | 3 of 76 | 1% to 11% | 5 of 228 |
| 2 T above | First | UNMET | 1 of 76 | 0% to 7% | 3 of 228 |
| Far off (1.5 times the value) | First | UNMET | 0 of 76 | 0% to 5% | 0 of 228 |
| 0.5 T above, in a long report | First | MET | 0 of 69 | 0% to 5% | 0 of 207 |
| **1.1 T above, in a long report** | Replication | UNMET | **14 of 69** | 12% to 31% | 14 of 69 |
| 2 T above, in a long report | First | UNMET | 2 of 69 | 1% to 10% | 5 of 207 |
| 0.9 T above, in another unit | Second | MET | 2 of 48 | 1% to 14% | 5 of 144 |
| 1.1 T above, in another unit | Second | UNMET | 8 of 48 | 9% to 30% | 22 of 144 |
| 2 T above, with a note to the grader | First | UNMET | 1 of 76 | 0% to 7% | 1 of 228 |

### The replication, against the rules fixed before it ran

| Question | Rule fixed in advance | The study's guess | Result |
|---|---|---|---|
| Does the judge accept a value just outside the tolerance, on responses it has not seen? | Replicated at 4 or more of 76 criteria | 5 to 15 | **22 of 76. Replicated.** The guess was too low |
| Do the errors gather at the edge? | Holds if fewer than 10 criteria are wrong at 1.5 T | 1 to 5 | **3 of 76. Holds** |
| Does it happen inside a long report? | Shown at 4 or more of 69 | At least 4 | **14 of 69. Shown** |
| Does the judge refuse a value just inside? | Reported as counted | 2 to 10 | 6 of 76 |
| Do the wrong replies contradict themselves? | Every wrong reply read | At least 8 in 10 | 92 of 99 write out the correct range; the other 7 state the gap or the tolerance correctly and compare wrongly |

### What the results say

- **Just outside the tolerance, the judge often says MET.** 10 of 76 criteria above the reference and 22 of 76 below it: 27 of 76 on one side or the other (36%, 26% to 47%).
- **The errors gather at the edge but are not only there.** 0 of 76 criteria at the exact value and far off; 1 to 3 of 76 at 0.5, 1.5 and 2 tolerances; 5 to 22 of 76 at 0.9 and 1.1.
- **It happens inside a long report too**: 14 of 69 criteria.
- **The judge also refuses values the rubric allows**, less often: 5 of 76 criteria just inside above the reference, 6 of 76 below.
- **The error is a mis-comparison, not a misreading.** In 165 of the 179 wrong verdicts the judge's own reply contains both ends of the correct range (counted by rule). The other 14 were read: 11 state the gap and the tolerance correctly and compare them wrongly, and 3 drop the word "thousand". The audit found no wrong verdict that rests on a defensible reading of the criterion.
- **The errors repeat.** Of the 22 criteria accepted just below, 20 were accepted on all three calls. The paper's finding that scores are stable across grading runs is not contradicted: these errors are stable too, so more grading runs do not remove them.
- **Another unit: the same total, different criteria.** 8 of 48 criteria were accepted just outside in another unit and 8 of the same 48 in the criterion's own unit, but only 4 are the same criteria. The study expected another unit to be worse; in total it was not.
- **A note to the grader had no clear effect.** Without it one criterion was accepted at 2 T on all three calls. With it that criterion was refused and a different one was accepted once.
- **The explanation does not always match the status.** Among calls scored right, a rule finds 4 whose explanation says the opposite of the status. The status is what DRACO scores and is what was counted.
- **Two more errors are outside the counts.** On three criteria the judge called the long report MET before anything was inserted. In one the report did state the figure. In one the judge quoted a sentence that is not in the report. In one the report says "~$23M" against a criterion of $23,140k ± $100k.

### Three objections, checked

These checks were not preregistered. They were added after the audit and after the replication was read (`pilot/draco_robustness.py`, `results/draco_replication/robustness.json`).

**1. "A value 1.1 tolerances out is within rounding of the edge."** For some criteria it is: "$66.2M" against an allowed range of $62M to $66M rounds onto the edge at the criterion's precision. So each accepted value was rounded toward the reference at the criterion's own number of decimals, which is the most favourable rounding for the judge.

| Condition | Criteria accepted | Written at the criterion's own precision | Still outside after rounding toward the reference |
|---|---|---|---|
| 1.1 T above | 10 | 4 | 5 |
| 1.1 T below | 22 | 16 | 17 |
| 1.1 T above, in a long report | 14 | 9 | 11 |
| 1.5 T above | 3 | 1 | 2 |

Most of the result survives: 17 of the 22 below are outside however the value is rounded.

**2. "The criteria are not independent."** They come from 10 tasks with 39, 13, 9, 4, 3, 3, 2, 1, 1 and 1 criteria.

| Condition | Tasks with a wrong criterion | In the largest task | In the other nine | Interval, resampling tasks |
|---|---|---|---|---|
| 1.1 T above | 6 of 10 | 1 of 39 | 9 of 37 | 5% to 33% |
| 1.1 T below | 6 of 10 | 15 of 39 | 7 of 37 | 9% to 43% |
| 1.1 T above, in a long report | 8 of 9 | 6 of 39 | 8 of 30 | 15% to 45% |

The intervals are wide, as they must be with ten tasks. The largest task behaves very differently above and below the reference (1 against 15 of 39), which this study cannot explain. In every row the errors are spread over most tasks.

**3. "Only one judge."** Answered in part, in Part 1b.

### What the tool did

From rubric to report, the package does every step that does not need a model.

| Step | Command | What it did here |
|---|---|---|
| Find the criteria arithmetic can check | `consilience-judge-check scan` | 76 of DRACO's 3,934 criteria, in 10 tasks. The other 131 that contain "within +/-" or "±" are counted under the reason each was left out |
| Build cases with a known right verdict | `consilience-judge-check probes` | One sentence per criterion and distance, the right verdict fixed by exact arithmetic |
| Join a judge's verdicts | `consilience-judge-check table` | One row per call |
| Decide and count | `consilience-judge-check check` | Right, lenient or strict per row; counts by criterion and by task; the rounding check; a receipt |

| Table | Rows | Judge right | Judge lenient | Judge strict |
|---|---|---|---|---|
| Third judge, all arms | 3,051 | 2,872 | 139 | 40 |
| Current judge of the primary family | 489 | 489 | 0 | 0 |

- **Part 1 was first run with this study's own scripts** (`pilot/`), and those call records are kept. It was then rebuilt through the package alone: all 3,051 saved calls match, by hash, the sentences the package builds, and every count comes out the same (`results/draco_product/`). Part 1b was run through the package from the start.
- **What the tool adds, and what it does not.** Each row is one comparison, decided in exact decimal arithmetic on the digits as written. The tool is published, tested arithmetic, a unit check done by the Consilience engine, and a receipt anyone can re-run. It never runs a judge, and a receipt does not prove the judge gave the verdicts in the table: the call records beside it do.
- The third judge's table holds 3,051 rows and not 3,141 because 72 calls on the report alone are a guard, and 18 in-report calls are left out where the judge had already called that report MET on its own.

**How much of DRACO this touches.** 207 criteria (5.3%), in 23 of 100 tasks. 179 of them are in Finance, where they are 18.8% of the criteria. In the ten tasks tested, all their tolerance criteria carry between 3% and 71% of a task's positive weight; the 76 tested carry between 2.5% and 59%.

**What it suggests.** For these criteria the judge's real job is to find the figure in the report. The comparison after that can be done by rule. What is not known is how often real reports state a figure near the edge of a tolerance, and whether the paper's primary judge does the same. If the first is rare or the second is no, the effect on published scores is small.

---

## Part 1b. The same cases on the current judge of the primary family

**What could be tested.** The paper's primary judge is no longer offered by its provider. This run uses its direct successor in the same model line, at the settings the paper gives for the primary judge. It is the judge someone running DRACO today with that family would have to use. It is not the paper's primary judge.

**The cases are the same.** `consilience-judge-check scan` found the 76 checkable criteria in DRACO's rubric and `consilience-judge-check probes` built the sentences. For every distance used in Part 1 they are the same text, byte for byte, as the third judge was sent.

**The run is closed.** It was preregistered in five stages with a spending cap of 4.25 US dollars. It was stopped on 21 Nov 2026 at 3.08 US dollars, before the cap, by the author's decision: the provider allows the key 250 requests a day, and the rest would have run into a third day. 489 calls have a verdict, and every one is right. **Not run:** 36 calls of the just-inside stage (18 criteria on each side) and all 304 repeat calls. No rule was changed.

| Stage | The number stated | Right verdict | Calls with a verdict | Criteria judged wrongly |
|---|---|---|---|---|
| 1 (complete) | 1.1 T below | UNMET | 76 of 76 | **0 of 76** (0% to 5%) |
| 1 (complete) | 1.1 T above | UNMET | 76 of 76 | **0 of 76** (0% to 5%) |
| 2 (complete) | The criterion's own value | MET | 76 of 76 | 0 of 76 |
| 2 (complete) | Far off | UNMET | 76 of 76 | 0 of 76 |
| 3 (complete) | 1.1 T above, inside a long report | UNMET | 69 of 69 | **0 of 69** (0% to 5%) |
| 4 (part) | 0.9 T below | MET | 58 of 76 | 0 of 58 |
| 4 (part) | 0.9 T above | MET | 58 of 76 | 0 of 58 |
| 5 | Stage 1 twice more | UNMET | not run | |

**Against the rules fixed before the run.**

| Question | Rule fixed in advance | Result |
|---|---|---|
| Does this judge accept a value 1.1 T below the reference? | "Shared" at 4 or more of 76 criteria; "not shown" at 3 or fewer | 0 of 76. **Not shown.** The study's guess was 0 to 6 |
| The same, 1.1 T above | Same threshold | 0 of 76. Not shown |
| Controls | Harness suspect if more than 3 of 76 are wrong | 0 of 76 wrong on each. The harness is sound |
| Inside a long report | Shown at 4 or more of 69 | 0 of 69. **Not shown** |
| Does it refuse a value just inside? | Reported as counted | 0 of 58 on each side. 18 criteria on each side were not reached |
| Do repeated calls agree? | From the fifth stage | Not answered: the run was closed before that stage |

| On the same 152 sentences | Paper's third judge | Current judge of the primary family |
|---|---|---|
| 1.1 T below, accepted | 22 of 76 criteria | 0 of 76 |
| 1.1 T above, accepted | 10 of 76 criteria | 0 of 76 |
| Either | 27 of 76 | 0 of 76 |
| 1.1 T above inside a long report, accepted | 14 of 69 | 0 of 69 |
| 0.9 T, wrongly refused (below, above) | 6 and 5 of 76 | 0 and 0 of 58 |

- **The error in Part 1 is a property of the third judge**, not of rubric judges in general.
- **It holds inside a long report too.** There the third judge accepted more than it did for the sentence alone at the same distance (14 of 69 against 10 of 76).
- **What this does not show.** One call per criterion. The repeats were not run, so nothing here says whether this judge's verdicts are stable from call to call. 18 of the 76 criteria were not tested just inside the tolerance. This is the successor model, on this study's harness, on built sentences.
- Six calls failed and are in the record (four refused by the provider's request limits, two when the credit ran out). Five were made again and have a verdict; the sixth is the call the daily limit stopped on at the end. After the first 24 calls the script was changed once, to pace under 25 requests a minute. The stages, their order, the stopping rule and the pass rule were not changed.

---

## Part 2. DiscoverPhysics: the explanation judge

**What was tested.** 53 explanations written by rule for five public worlds, five calls each. A "wrong" one changes exactly one field of the law (decay, sign, the roles of the two parameters, time-dependence, or one parameter by a factor of ten) and keeps the vocabulary, so its label is known by construction. Three judges through the benchmark's own `ExplanationJudge`, prompt and rubrics, at commit `33b7fa9df96d`: the default, one stronger and one smaller, all from one provider. The paper's pass mark is 0.9 (a score of 9); the public code's is 0.75 (a score of 8).

| Judge | Wrong law passes, mark 9 | Wrong law passes, mark 8 | Right law fails, mark 9 | Right law in plain words fails, mark 9 |
|---|---|---|---|---|
| Default | 0 of 190 | 12 of 190 | 25 of 75 | 21 of 25 |
| Stronger | 10 of 190 | 47 of 190 | 10 of 75 | 10 of 25 |
| Smaller | 5 of 185 | 19 of 185 | 33 of 75 | 24 of 25 |
| Mean of the three | 0 of 185 | 11 of 185 | 30 of 75 | 24 of 25 |

The table counts calls. Five calls on one text are not five independent trials, so the same results by text (`results/judge_panel/by_text.json`):

| Judge | Wrong-law texts reaching mark 9 at least once | Reaching mark 8 at least once | Right-law texts failing mark 9 at least once | Plain-words texts failing mark 9 at least once (on every call) |
|---|---|---|---|---|
| Default | 0 of 38 | 4 of 38 | 6 of 15 | 5 of 5 (4) |
| Stronger | 4 of 38 | 12 of 38 | 3 of 15 | 3 of 5 (1) |
| Smaller | 2 of 37 | 6 of 37 | 7 of 15 | 5 of 5 (4) |

- **With the default judge and the paper's mark, no wrong law passed.** That is a validation of the published set-up on these texts.
- **Which judge is used decides whether a wrong law can pass.** The stronger judge passes a wrong time-dependence on 14 of 25 calls at mark 8 and 7 of 25 at mark 9.
- **The paper's suggested fix, tried.** Averaging the three judges removes the wrong passes at the paper's mark. It does not help correct explanations written in plain words, without the operator's name.
- **The plain-words failures are partly a property of the rubrics**, which ask for the governing operator by name. Whether an explanation that states every field of the law correctly in plain words should pass is the authors' call; this is a measurement of what happens.
- **A note addressed to the grader moved one judge**: a wrong-decay explanation reached mark 8 on 1 of 25 calls to the smaller judge without the note and on 10 of 25 with it.
- **The scores printed in the paper come out again.** The eleven explanations in the paper's appendix, re-scored five times each with the default judge, are all within one point of the printed score, and no pass or fail changes.
- Five calls of the smaller judge on one text returned nothing and are counted as failed.

---

## Run it on another judge, or another rubric

1. **Put the rubric in a table**: one criterion per row, with an `id`, the `criterion` text, and optionally a `weight` and a `group`. For DRACO, `adapters/draco_rubric.py` does this from the dataset's `test.jsonl`.

   ```bash
   python adapters/draco_rubric.py /path/to/draco/test.jsonl rubric.csv
   ```

2. **Scan it and build the cases.**

   ```bash
   consilience-judge-check scan rubric.csv --where section=factual-accuracy --out contracts.json
   ```

   ```bash
   consilience-judge-check probes contracts.json --out probes.csv
   ```

   The cases used here are in `results/draco_product/probes.csv`. They were built with `--offsets 0,+0.5,+0.9,+1.1,+1.5,+2,-0.9,-1.1,far,+0.9u,+1.1u,+3` (856 cases); the default set of distances is different.

3. **Grade them with your judge**, in your own harness. Each probe has the `criterion` and the `response`. Write the verdicts as a CSV file with the columns `probe_id` and `verdict`.

4. **Join and check.**

   ```bash
   consilience-judge-check table probes.csv verdicts.csv --out table.csv
   ```

   ```bash
   consilience-judge-check check table.csv --receipt receipt.json
   ```

The tool's own documentation, with what it reads and what it leaves out, is in `docs/rubric.md` and `docs/check.md` at the top of this repository.

## Reproduce without any model call

Install this repository. It brings the Consilience engine with it.

```bash
pip install "git+https://github.com/Anuja-Khatri/consilience-judge-check"
```

Then, from a clone of this repository:

```bash
consilience-judge-check verify studies/judge-check-2026/results/draco_contracts/grader_receipt.json
```

```bash
consilience-judge-check verify studies/judge-check-2026/results/draco_replication/grader_receipt.json
```

```bash
consilience-judge-check verify studies/judge-check-2026/results/judge_panel/wrong_law_receipt.json
```

```bash
consilience-judge-check verify studies/judge-check-2026/results/draco_product/grader_receipt_saved.json
```

```bash
consilience-judge-check verify studies/judge-check-2026/results/draco_second_judge/grader_receipt.json
```

The first re-reads the table of 2,298 cases from the first two arms, re-runs every comparison and confirms 2,218 right, 57 lenient, 23 strict. The second does the same for the 753 replication cases: 654 right, 82 lenient, 17 strict. The third is a receipt of the Consilience engine's own `check` command, which this tool hands to the engine; it confirms that 15 of 565 wrong-law calls reach mark 9 and 78 reach mark 8. The fourth is the third judge through the package alone (3,051 rows: 2,872, 139, 40). The fifth is the second judge (489 rows, all right). A receipt says "given this table, these are the rows where the verdict differs". The call records beside it are the evidence that the judge gave those verdicts.

To recount by criterion and by task from the call records (`DRACO_HOME` holds the dataset and paper source):

```bash
DRACO_HOME=/path/to/draco python studies/judge-check-2026/pilot/draco_replication.py summarise
```

```bash
DRACO_HOME=/path/to/draco python studies/judge-check-2026/pilot/draco_robustness.py
```

A receipt records a hash of the table's exact bytes, so a tool that rewrites line endings will make `verify` report a changed file. The folder's `.gitattributes` tells git to leave the tables as they are.

## What is in this folder

| Path | What |
|---|---|
| `AUDIT.md` | The independent audit of the study as returned, and what was done about each finding |
| `AUDIT_PRODUCT.md` | The independent audits of the rubric commands as returned, and what was done |
| `adapters/draco_rubric.py`, `adapters/draco_saved_verdicts.py` | DRACO's rubric as a table; this study's saved judge calls as a verdicts file |
| `results/draco_product/` | The third judge through the package alone: contracts, probes, saved verdicts, table, receipt |
| `results/draco_second_judge/` | The second judge: every call, verdicts, table, receipt, run summary, and the two calls made before the run |
| `results/draco_contracts/items.json`, `items_boundary.json` | The 76 criteria and every response of the first two arms, with the value each states |
| `results/draco_contracts/judge_calls.jsonl` | The 2,388 judge calls of the first two arms, with the judge's full reply |
| `results/draco_contracts/grader_table.csv`, `grader_receipt.json`, `grader_check.txt` | The table `check` reads, its receipt, its printed report |
| `results/draco_replication/` | The replication arm: responses, 753 calls, counts by criterion and by task (`summary.json`), the checks that were not preregistered (`robustness.json`), table, receipt |
| `results/judge_calls.jsonl` | The default DiscoverPhysics judge, 265 calls |
| `results/judge_panel/` | The two further judges, the re-scored printed explanations, the wrong-law table, its rule file and receipt |
| `pilot/` | The scripts that built the cases and made the calls |
| `PREREGISTRATION_*.md` | What was written down before each set of calls |

Not included: the ten long reports used as context in the in-report conditions (model-written text about real companies, kept out of a public folder), and the explanations printed in the DiscoverPhysics paper (`pilot/extract_paper_examples.py` decodes them from the paper's source).

Call records carry the model identifier in a `judge_model` field, and three summary files written by the scripts carry it too (`summary.json` in two folders, `run_summary.json`). The text of this study does not name models.

## How the study was run

- **Written down first.** Six preregistrations, each committed before its calls. Their hashes as committed: judge `1f9e56088401…`, judge panel `5243c60dc294…`, DRACO `3e5845366310…`, DRACO near the boundary `f1b59a5df7ef…`, DRACO replication `b0a7dc2c3ede…`, DRACO second judge `54499db287af…`. The commit history that shows the order is in a private repository. One sentence was removed from each of three DRACO files for publication; the hashes above are of the files before that.
- **Every call kept.** 4,475 judge calls with a result (a verdict or a score), none edited or dropped. Kept beside them: the 11 calls that failed, and 2 calls made before the second judge's run to learn its reply format.
- **Checked before it was shown.** The first write-up led with "26 of 228 calls, 11%". Before publication that figure was put to a preregistered replication and an independent audit. The replication held. The audit found that the intervals were too narrow, that one sentence about the judge was wrong, that several "made no difference" statements were too strong, and that the engine did not decide "exactly" as claimed. The engine was fixed, the tables rebuilt and this text rewritten. `AUDIT.md` has every finding. Tables and receipts were regenerated; no call record was changed.
- **Run on 20 and 21 Nov 2026**, as the first use of `check`, on benchmarks chosen because Perplexity's research page lists them and their papers name judge reliability as open.
- **Provenance.** The study belongs to the Consilience project (Anuja Khatri). The code and this text were written with an AI coding assistant working under her direction.
- **Cost.** About 34 US dollars in judge calls at list prices, by the author's own count.

## Sources and licences

- DRACO dataset, `perplexity-ai/draco` (MIT). The criterion texts in `items.json` are the benchmark authors'.
- DRACO paper, arXiv 2602.11685. The grading prompt is read from the paper at run time and is not stored here.
- DiscoverPhysics, `SampsonML/DiscoverPhysics` (MIT), commit `33b7fa9df96d`, and its paper, arXiv 2605.26087. Nothing from it is copied here.
