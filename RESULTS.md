# Results on one page

`consilience-judge-check` tests a rubric judge on the one kind of criterion whose right verdict needs no opinion: a stated number with a stated tolerance. It builds the test from the rubric itself, with no human labels and no second model.

This page is what it found on two public benchmarks: **DRACO** (Perplexity) and **DiscoverPhysics**. Every number here is in the full write-up, with its limits: [studies/judge-check-2026](studies/judge-check-2026/README.md).

## DRACO: does the judge apply the tolerance the rubric states?

| # | Finding | The numbers |
|---|---|---|
| 1 | **One of the paper's judges accepts values the rubric rules out.** | Run as the paper specifies, the third judge said MET to a value just outside the stated tolerance for **27 of 76** criteria |
| 2 | **It writes the right range, then compares wrongly.** | In **165 of its 179** wrong verdicts, its own reply contains the correct range. One reply: "The response states the exam fee as $82, which falls within the acceptable range of $93 ± $10 ($83–$103)." |
| 3 | **It is consistent, and consistently wrong.** | Of the 22 criteria it got wrong below the reference, **20 were wrong on all three calls**. Running the judge again would not have shown the problem |
| 4 | **The figure was repeated before it was published.** | A second run on new values, with the pass rule fixed first at 4 or more of 76: **22 of 76**. The study's own guess, 5 to 15, was too low |
| 5 | **A long report does not help.** | With the value placed inside a long report: **14 of 69**, against 10 of 76 for the same sentence alone |
| 6 | **For this judge, the error goes when it is allowed to reason.** | Same judge, same sentences, reasoning switched on: **0 of 76** below the reference and **1 of 76** above. Changing only the temperature: still **24 of 76** |
| 7 | **The judge family behind DRACO's main results is clean.** | The current judge of the paper's primary family: **697 calls, none wrong**. Just outside, just inside, on the value, far off, inside a long report, and on repeat calls |
| 8 | **A replaced judge can be re-checked for a few dollars.** | DRACO's primary judge had been withdrawn by its provider. Its successor went through the same test for about **4 US dollars**, with nothing rebuilt |
| 9 | **A real share of the rubric could be scored by rule.** | **207 of 3,934** criteria mention a tolerance. In Finance that is **19%** of the criteria |

## DiscoverPhysics: does the explanation judge pass a wrong law?

| # | Finding | The numbers |
|---|---|---|
| 10 | **Which judge is used decides whether a wrong law passes.** | Default judge: **0 of 38** wrong-law explanations reach the paper's pass mark. A stronger judge from the same provider: **4 of 38**, and **12 of 38** at the mark in the public code |
| 11 | **Correct explanations in plain words fail.** | All **5 of 5** fail at least once under the default judge, 4 of them on every call |
| 12 | **A note written to the grader moves a judge.** | The same wrong explanation reached the public code's mark on **1 of 25** calls without the note, and on **10 of 25** with it |
| 13 | **The paper's own suggested fix was tried.** | Averaging three judges removes the wrong passes. It does not help the plain-words failures |
| 14 | **The paper's printed scores come out again.** | All eleven printed explanations, re-scored, land within one point of the printed score, and no pass or fail changes |

## How it was done

- **Rules first.** Seven preregistrations, each committed before its calls.
- **Every call kept.** 4,911 judge calls, plus the 11 that failed.
- **Every result re-runs.** Eight receipts, checked by `consilience-judge-check verify`, and 200 tests.
- **Checked by others.** Seven checks by separate AI sessions, kept as returned. Three of them broke the rubric reader, and it was rebuilt each time.
- **Cost.** About 37 US dollars in judge calls.

## What this does not show

- **Nothing about any system's score or rank.** The test sentences are built for the test. They are not real reports.
- **The sample is small.** 76 criteria from 10 tasks, one of which holds 39. DiscoverPhysics: 38 and 5 texts in five worlds.
- **Finding 6 is narrow.** One judge, one call per sentence, on values just outside a tolerance only. It does not show why the two judges differ.
- **Finding 7 is the successor** of the paper's primary judge, not that judge.
- **The rubric reader is narrow.** It has met one rubric, and its final version has not been audited.
- **No person has reviewed this yet.**

Both benchmarks publish their rubrics, prompts and code. That is the only reason this check was possible.

## Run it yourself

```bash
pip install "git+https://github.com/Anuja-Khatri/consilience-judge-check"
```

What the tool does and how to use it on another rubric or another judge: [README.md](README.md).
