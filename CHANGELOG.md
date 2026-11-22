# Changelog

## The study, 22 Nov 2026: the run on the second judge is finished

No code changed. The run on the second DRACO judge had been closed on 21 Nov before its spending cap. It was reopened on 22 Nov by the author's decision and taken to the cap.

| | |
|---|---|
| Calls with a verdict | 697, every one right |
| Just inside the tolerance | Now complete: 76 of 76 criteria on each side, none wrongly refused |
| Repeat calls on the just-outside sentences | 172 of the 304 planned, which is what the cap allowed. Every criterion has two calls on each side and 10 have three. None was accepted on any call |
| Failed calls | Six in all, each made again |
| In the whole study | 4,911 judge calls with a result, 11 failed, all kept |

A separate session recounted the run from the call records before these numbers were published, and reproduced every count (`studies/judge-check-2026/AUDIT_SECOND_JUDGE.md`). It also listed limits that Part 1b of the write-up now states: the in-report result is weaker than the single-sentence one, the intervals treat criteria from 10 tasks as independent, the run was counted after each batch, and the script was changed twice after the first calls, not once.

## The study, 21 Nov 2026: the third judge with its reasoning switched on

No code changed. A new, preregistered experiment was added to the study (Part 1c of its write-up).

| Setting of the paper's third judge | Criteria accepted at 1.1 tolerances below | At 1.1 above |
|---|---|---|
| As the paper runs it: reasoning off, temperature 0 (first call) | 22 of 76 | 9 of 76 |
| Reasoning off, default temperature (the control) | 24 of 76 | not run |
| Reasoning on | 0 of 76 | 1 of 76 |

- By the rules fixed before the run: for this judge, the reasoning step removes the error.
- It does not show that the judge is accurate with reasoning on (only values just outside a tolerance were tested), and it does not show why the two judges differ.
- 228 calls, none failed. A separate session recounted it and reproduced every count: `studies/judge-check-2026/AUDIT_REASONING.md`.
- In the whole study: 4,703 judge calls with a result, 11 failed, all kept. Seven preregistrations.
- One test added: the two new receipts re-run to these counts. 200 tests.

## The study, 21 Nov 2026: the run on the second judge is closed

No code changed. The last calls on the second DRACO judge were made and counted, and the run was closed before its spending cap by the author's decision, when the provider's limit of 250 requests a day would have carried it into a third day.

| | |
|---|---|
| Calls with a verdict | 489, every one right |
| Complete | Just outside the tolerance (0 of 76 accepted on each side); exact and far-off values (all right); just outside, inside a long report (0 of 69 accepted) |
| Part done | Just inside the tolerance: 58 of 76 criteria on each side, none wrongly refused |
| Not run | 18 criteria just inside, and all the repeat calls |
| In the whole study | 4,475 judge calls with a result, 11 failed, all kept |

## 0.1.1 (21 Nov 2026)

Corrections after an independent check of this repository by a separate session. Its report, as returned, and what was done about each finding: [AUDIT_MOVE.md](AUDIT_MOVE.md).

**One behaviour was put back.** In 0.1.0 a currency amount written with a prefix (`kUSD`) was refused in the three usual places only. Written inside a value cell, or in a tolerance with no ordinary space before the unit, it was read as 1,000 USD and the row was decided. Before the move such rows were always refused. Now the Consilience engine itself applies its no-prefix rule to the currency codes, as it did before the move, so the rows are refused again with the same wording. No table in the study has such a row, and no result changed.

| Check after the correction | Result |
|---|---|
| The checker's 51 tables (12,665 rows), old code against new | No difference in any count, disagreement or undecided row |
| `read_criterion` on 14,163 inputs (the auditors' hostile criteria and every DRACO criterion), old against new | No difference |
| A receipt the old code wrote for a table with a prefixed currency | Re-runs unchanged |
| The tests, run from the repository and from another folder | 199 pass |

**Also changed.**

- `verify` now also looks for a receipt's table beside the receipt, and checks it by hash, so the study's receipts re-run from any folder and not only from the top of the repository.
- A `check` receipt with no engine version is refused again, as before the move. Only `judge_check_version` may be missing.
- Three paths that carried the name of a model family were renamed (see `PROVENANCE.md`), and the second judge's receipt was written again at its new path.
- Statements corrected in `README.md`, `PROVENANCE.md`, `docs/` and the study write-up. The largest: two source hashes in `PROVENANCE.md` were the wrong way round; two commands on the front page lacked `--out`; the study counted 4,464 calls with a verdict where the right figure is 4,459 calls with a result and 10 failed calls.

## 0.1.0 (21 Nov 2026)

The first version as a package of its own.

**Where it came from.** The commands were written on 20 and 21 Nov 2026 as part of the `consilience` package, on a working branch that was not published. They were moved here so that the tool and its first study have one home, named for what the tool does.

| Then | Now |
|---|---|
| `consilience rubric scan` | `consilience-judge-check scan` |
| `consilience rubric probes` | `consilience-judge-check probes` |
| `consilience rubric table` | `consilience-judge-check table` |
| `consilience grader-check` | `consilience-judge-check check` |
| `consilience verify` | `consilience-judge-check verify` |

**What changed in the code.**

- The two modules now import the Consilience engine as a dependency, pinned to one public commit.
- The five currency codes (USD, EUR, GBP, INR, JPY) are registered by this package on the engine's unit registry. The rule that a currency code takes no prefix was checked in this package in 0.1.0, incompletely; since 0.1.1 the engine applies it.
- New receipts carry `judge_check_version` beside the engine's `consilience_version`. Receipts written before the move carry only the second, and still verify. (In 0.1.0 that held for the study's receipts but not for a table with a prefixed currency; see 0.1.1.)
- The receipt formats are unchanged. In a receipt, `command` keeps the names the formats gave these operations from the start (`rubric scan`, `rubric probes`, `grader-check`).
- The comment line at the head of a probes file and of a table names the new command. `verify` also accepts a probes file with the earlier line.
- `verify` hands a receipt written by the engine itself to the engine's own `verify`.
- Nothing else was meant to change. The reading rules, the sentence builder and the arithmetic are as they were. The independent check found one unintended change, described under 0.1.1.

**How the move was checked.** Run on 21 Nov 2026, in a clean environment with the engine installed from its public commit.

| Check | Result |
|---|---|
| The 197 tests (199 since 0.1.1) | All pass |
| The six receipts in the study, re-run by the moved code | All re-run to the same result, unchanged |
| The contracts file, re-run from DRACO's rubric | Same result: 3,934 criteria read, 207 mention a tolerance, 76 accepted |
| The preregistered file of test sentences, rebuilt from the contracts | Byte for byte the same (sha256 `147522f41376131e…`) through `verify` and the tests, which rebuild it with the comment line it was first written with. The `probes` command today writes the same rows under a new first line |
| The third judge's 3,051 graded cases, joined and decided again | 2,872 right, 139 lenient, 40 strict, as before |
| The second judge's 473 graded cases at that time, joined and decided again | 473 right, as before |
| The study folder | Every file byte for byte as on the working branch, except its `README.md` (true of 0.1.0; for the renames made in 0.1.1 see `PROVENANCE.md`) |
