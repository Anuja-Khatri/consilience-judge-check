# consilience-judge-check

**Where a rubric's right answer is arithmetic, is the judge right?**

**What it found on two public benchmarks, on one page: [RESULTS.md](RESULTS.md).**

More and more work is scored by a rubric and a judge, and the judge is often a language model. Most of what a rubric asks needs judgement. Some of it does not. A criterion such as "States Q3 revenue as $30.8B (within +/- $0.5B)" has one right verdict, and it is fixed by arithmetic.

`consilience-judge-check` reads a rubric, finds those criteria, builds test responses whose right verdict is known, and reports where a judge's verdict differs. It needs no human labels. It runs no judge and no model: you run your judge on the test responses in your own harness and hand back its verdicts.

It is a Consilience tool. The Consilience engine (the `consilience` package) reads the values and units and hashes the receipts. This package finds the checkable criteria, builds the test and decides each case.

| Step | Command | What you get |
|---|---|---|
| Find the criteria arithmetic can check | `consilience-judge-check scan rubric.csv --out contracts.json` | How many there are, how much of the rubric's weight they carry, and every other criterion counted under the reason it was left out |
| Build the test | `consilience-judge-check probes contracts.json --out probes.csv` | Short responses that state a value at a known distance from the reference: on it, just inside the tolerance, just outside, far off |
| Join your judge's verdicts | `consilience-judge-check table probes.csv verdicts.csv --out table.csv` | One row per graded case |
| Decide and count | `consilience-judge-check check table.csv --receipt receipt.json` | Each row right, lenient or strict; counts by criterion; a receipt |
| Re-run a result | `consilience-judge-check verify receipt.json` | Whether the receipt re-runs to the same answer |

## What it adds to the usual ways of checking a judge

The arithmetic here is simple, and anyone could do it by hand for one criterion. What the tool adds is in the right-hand column.

| Usual check | What it shows | What it cannot show | What this tool adds |
|---|---|---|---|
| Run the judge several times | Whether it is consistent | Whether it is right. In the first study, one judge gave the same wrong verdict on every call for 20 of the 22 criteria it got wrong below the reference | A right verdict for every case, fixed by the rubric's own number and tolerance |
| Compare several judges | Whether they agree | Which judge is right | For 27 of 76 criteria, two judges gave different verdicts on a value just outside the tolerance. The tool says which is right each time |
| Compare the judge with expert labels | Which is right, on the labelled sample | Anything outside the sample. Labels take experts' time, and experts disagree | No labels. The answer key is the rubric itself, so the test is public and anyone can run it again |
| A script written for the occasion | An answer, once | Whether the script is right | The cases are built from the rubric by one command. Each row is decided in exact decimal arithmetic. What cannot be read exactly is left out and listed, not guessed. Every result has a receipt that re-runs. The audit records are in this repository |

**When a judge is replaced.** Models used as judges are withdrawn by their providers. The same test can be put to the replacement with nothing rebuilt. In the first study that took 697 calls and about 4 US dollars.

**What it does not add.** Anything about the criteria that need judgement, which is most of any rubric. And it checks; it does not discover. It finds where a judge misapplies a stated tolerance. It finds nothing about the work being judged.

## The first study: two public benchmarks

Full write-up, with limits first: [studies/judge-check-2026](studies/judge-check-2026/README.md).

| Benchmark | Question | Result |
|---|---|---|
| DRACO (Perplexity) | Does the judge apply the tolerance a criterion states? | **It depends on the judge.** On the same 76 criteria and the same sentences, the paper's third judge accepted a value just outside the stated tolerance for 27 criteria. The current judge of the paper's primary family accepted none, including inside a long report (0 of 69 against 14 of 69). Both were right on exact and far-off values. With its reasoning switched on, the third judge stopped too: 0 of 76 below the reference and 1 of 76 above, where changing only the temperature left 24 of 76 |
| DiscoverPhysics | Does a wrong law pass the explanation score, and does it depend on which judge is used? | With the default judge, 0 of 38 wrong-law explanations reach the paper's pass mark. With a stronger judge from the same provider, 4 of 38 do. All 5 correct explanations written in plain words fail at least once under the default judge |

**For DRACO's authors, the short version.** The judge family behind the paper's main results does not show this error on these cases. The third judge, used in the paper's judge-comparison appendix, does, as the paper runs it: with reasoning disabled. With reasoning switched on it does not. Nothing here says any system's score or rank would change.

Both benchmarks publish their rubrics, prompts and code, which is the only reason this check was possible.

## What a first reading might assume

| It would be natural to assume | What is the case |
|---|---|
| This says DRACO's results are wrong | It does not. The judge family behind the paper's main results shows no error on these cases |
| A second model is judging the judge | No model decides anything. The tool runs no model. Each verdict is a comparison of two numbers from the rubric |
| The test covers the rubric | It covers the criteria that state a number and a tolerance in one wording: 76 of DRACO's 3,934. The rest needs judgement and is untouched |
| The judges tested are the paper's three | One is: the third, at the paper's settings and, as a separate experiment, with its reasoning switched on. The primary judge has been withdrawn by its provider, so its successor was tested. The second was not tested |
| Switching reasoning on makes that judge accurate | The study shows less than that. With reasoning on it stopped accepting values just outside a tolerance. Values inside a tolerance were not put to it in that setting |
| The sample is large | 76 criteria from 10 tasks, and one task holds 39 of them |
| The rubric reader works on any rubric | It reads a narrow pattern and has been tried on one rubric. It writes a review list for a person to check |
| People have reviewed this | Not yet. Seven checks were done by separate AI sessions. Three of them broke the rubric reader, and the reader's final version has not been audited. One found that the move to this repository had changed one behaviour, since put back. Two recounted the later runs from their call records. The records are kept as returned |
| This is long-standing work | The Consilience engine is older. This tool and its study were built in November 2026, with an AI coding assistant working under the author's direction |

## Install

Needs Python 3.10 or newer.

```bash
pip install "git+https://github.com/Anuja-Khatri/consilience-judge-check"
```

This also installs the Consilience engine from its public repository, at one fixed commit, so that every result here re-runs the same.

A worked example with made-up data, from a six-line rubric to a report: [docs/rubric.md](docs/rubric.md). What `check` reads, how each row is decided, and what a receipt holds: [docs/check.md](docs/check.md).

## Check the study yourself

No model call is needed.

```bash
git clone https://github.com/Anuja-Khatri/consilience-judge-check && cd consilience-judge-check
```

```bash
pip install -e ".[test]"
```

```bash
python -m pytest
```

The 200 tests include more than a hundred of the hostile criteria the auditors wrote, and tests that rebuild the study's test sentences byte for byte and re-run its receipts. To re-run one receipt by hand:

```bash
consilience-judge-check verify studies/judge-check-2026/results/draco_product/grader_receipt_saved.json
```

That re-reads the third judge's 3,051 graded cases, decides every row again and says whether the result is the same as recorded. To see the counts themselves (2,872 right, 139 lenient, 40 strict):

```bash
consilience-judge-check check studies/judge-check-2026/results/draco_product/table_saved.csv
```

## Limits

- **The rubric reader is narrow and is not proven.** It reads criteria that start with "States", end with "(within +/- T)" and give a dollar amount, a percentage or a count. Everything else is left out and counted. Three audits each found hostile criteria it misread; it was rewritten after each, and the final version has not been audited. Read the review list it writes (`scan --review`).
- **It has met one real rubric.**
- **The study uses built sentences, not real reports**, and a small sample.
- **The second judge was given fewer distances than the third**, and two calls on each just-outside sentence where the third had three. Every repeated call agreed.
- **The reasoning experiment tested one judge, one call per sentence, on values just outside a tolerance only.** It does not show why the two judges differ.
- **A receipt says "given this table, these rows differ from the arithmetic".** It does not prove the judge gave the verdicts in the table. The call records kept beside it are the evidence for that.
- **The engine is pinned to a development commit** of `consilience-core` (0.2.0.dev0), not to a release.
- **No person has reviewed this yet.** Every audit so far was done by a separate AI session.

## What is in this repository

| Path | What |
|---|---|
| `src/consilience_judge_check/` | The tool: `rubric.py` (scan, probes, table), `grader.py` (check), `verify.py`, `units.py` (currency codes), `cli.py` |
| `tests/` | 200 tests |
| `docs/rubric.md`, `docs/check.md` | What problem each command solves, who it is for, what is read and what is left out, limits |
| `studies/judge-check-2026/` | The first study: write-up, the audit records as returned, seven preregistrations, scripts, every judge call, tables, receipts |
| `RESULTS.md` | The findings on one page, with what they do not show |
| `PROVENANCE.md` | Where each thing came from |
| `CHANGELOG.md` | What changed, including how the move to this repository was checked |
| `AUDIT_MOVE.md` | The independent check of this repository after the move, as returned, and what was done about each finding |

## How it was made

- **By whom.** The work belongs to the Consilience project (Anuja Khatri). The code and text were written with an AI coding assistant working under her direction.
- **When.** The study was run on 20 and 21 Nov 2026. The commands were first written as part of the `consilience` package and were moved here on 21 Nov 2026, so that the tool and its study have a home of their own. The move changed no result: [CHANGELOG.md](CHANGELOG.md) says how that was checked.
- **What the history here does and does not show.** Each preregistration was committed before its run in a private working repository. This repository was assembled afterwards, so its own history does not show that order.

## Licence

Code: MIT ([LICENSE](LICENSE)). Data, records and text: CC BY 4.0 ([LICENSE-DATA](LICENSE-DATA)). The criterion texts quoted in the study are the DRACO authors' (`perplexity-ai/draco`, MIT). See [PROVENANCE.md](PROVENANCE.md).
