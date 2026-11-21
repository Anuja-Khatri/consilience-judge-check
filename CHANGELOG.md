# Changelog

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
- The five currency codes (USD, EUR, GBP, INR, JPY) are registered by this package on the engine's unit registry. The rule that a currency code takes no prefix is checked here.
- New receipts carry `judge_check_version` beside the engine's `consilience_version`. Receipts written before the move carry only the second, and still verify.
- The receipt formats are unchanged. In a receipt, `command` keeps the names the formats gave these operations from the start (`rubric scan`, `rubric probes`, `grader-check`).
- The comment line at the head of a probes file and of a table names the new command. `verify` also accepts a probes file with the earlier line.
- `verify` hands a receipt written by the engine itself to the engine's own `verify`.
- Nothing else. The reading rules, the sentence builder and the arithmetic are as they were.

**How the move was checked.** Run on 21 Nov 2026, in a clean environment with the engine installed from its public commit.

| Check | Result |
|---|---|
| The 197 tests | All pass |
| The six receipts in the study, re-run by the moved code | All re-run to the same result, unchanged |
| The contracts file, re-run from DRACO's rubric | Same result: 3,934 criteria read, 207 mention a tolerance, 76 accepted |
| The preregistered file of test sentences, rebuilt from the contracts | Byte for byte the same (sha256 `147522f41376131e…`) |
| The third judge's 3,051 graded cases, joined and decided again | 2,872 right, 139 lenient, 40 strict, as before |
| The second judge's 473 graded cases so far, joined and decided again | 473 right, as before |
| The study folder | Every file byte for byte as on the working branch, except its `README.md` |
