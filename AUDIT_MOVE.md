# The independent check of this repository after the move

On 21 Nov 2026 the tool and its study were moved into this repository. A separate AI session, which had not written the code, was then asked to find out by running things itself whether the repository works as its documents say and whether the move changed any behaviour. It was given the code and the data, not a conclusion.

- **It found one real change in behaviour** (findings 1 and 2), several wrong or overstated statements (3, 4, 6, 7), and things worth cleaning (5, 8, 9).
- **It checked version 0.1.0** (commit `bfb7d65`). The corrections are version 0.1.1.
- **It was done by an AI session, not by a person.**

Its report is below as it was returned. Three kinds of words are replaced, and nothing else is changed: paths on the machine it ran on are shortened to `WORK`, "the old repository" or "the dataset folder"; the name of a model family is written `[family]`; and the name of the AI assistant in a commit's author line is written in square brackets.

## What was done about each finding

| # | Finding | What was done |
|---|---|---|
| 1 | After the move, a currency amount written with a prefix (`kUSD`) inside a value cell, or in a tolerance with no ordinary space before the unit, was read as 1,000 USD and the row was decided. Before the move such rows were refused. 115 of the checker's 12,665 rows | **Put back.** The Consilience engine itself now applies its no-prefix rule to the currency codes, as before the move. The checker's own comparison was run again on its 51 tables: no difference in any count, disagreement or undecided row. A test holds the checker's cases. No table in the study has such a row, so no result was affected |
| 2 | For such rows the wording of the "could not decide" entries differed from before the move, so a receipt the old code wrote for such a table did not re-run | **Gone with 1.** The same engine code now refuses the row, with the same wording. The checker's old receipt re-runs unchanged |
| 3 | Two source hashes in `PROVENANCE.md` were the wrong way round | **Corrected.** `PREREGISTRATION_DRACO.md` has the same swap and is left as written; `PROVENANCE.md` says so |
| 4 | Two commands in the front page's table failed as written (no `--out`). Exit code 2 was not documented | **Corrected.** The table gives full commands. Exit code 2 is documented |
| 5 | The study's `check` receipts re-ran only from the top of the repository | **Changed.** `verify` also looks for the table beside the receipt and checks it by hash. The tests pass from any folder |
| 6 | Overstated or imprecise claims | **Each corrected.** The tests hold more than a hundred of the auditors' hostile criteria, not all of them. `verify` says whether a result is the same; `check` prints the counts. The test sentences rebuild byte for byte through `verify` and the tests, not through the `probes` command, which writes a new first line. What is stored from the dataset is listed in full. The adapter with unused code is described in full. The study has 4,459 calls with a result and 10 failed calls, not 4,464 with a verdict. Both write-ups now give the same run dates. The cost is marked as the author's own count |
| 6 | Could not confirm: that each preregistration was committed before its run | **Unchanged, and said openly.** That order is in a private working repository. This repository's history does not show it |
| 7 | Smaller mismatches between the documents and the tool | **Corrected**: shortened outputs are marked as shortened; "two audits" is three; `--lead` replaces the default and the document says so; the help text of `verify` mentions the engine's receipts; the study write-up gives the distances its test file was built with. **Left as it is:** a contracts file whose rubric is missing reports FAILED, where a `check` receipt whose table is missing reports an error |
| 8 | `verify` does not compare version fields | **Documented** in `docs/check.md`. One part was tightened: a `check` receipt with no engine version is refused again, as before the move |
| 9 | A model family's name in three paths and in one sentence of an audit record, while the study said its text names no models | **Renamed and corrected** (see `PROVENANCE.md`). The summary files that carry a model identifier are now listed beside the call records |
| 9 | `LICENSE-DATA` named kinds of material this repository does not hold | **Corrected** |
| 9 | The commit's author line and trailer name the AI assistant | **Left.** Those lines are added to every commit the assistant makes. The prose says the work was written with an AI coding assistant |

## The report, as returned

AUDIT REPORT: consilience-judge-check 0.1.0 (commit bfb7d6549a0d), checked 21 Nov 2026, 15:26 to 15:57 UTC

Nothing was fixed, committed, pushed or edited in either repository. All work is in a scratch folder (called WORK below). The clone I was given and the old repository both still show a clean `git status`.

Summary: the install, the 197 tests, the worked examples and every study receipt behave as documented, and the study's own tables give identical results old vs new. The move did change behaviour for one thing: currency codes with a prefix. The other findings are wrong or overstated statements in the documents.

### FINDINGS, most important first

1. The move changed how a prefixed currency (kUSD) is handled: NEW decides rows that OLD refused.

- What I ran: my own comparison of `check_grader` OLD vs NEW on 40 readable tables, 12,665 rows (WORK/cmp/runner.py, diff.py, rowdiff.py; tables from WORK/cmp/make_tables.py).
- Expected: docs/check.md lines 153-155 say "no prefix is read (`kUSD`)". CHANGELOG.md line 20 says the rule "is checked here", and line 25 says "Nothing else" changed.
- What happened: 115 rows that OLD left undecided are decided by NEW, with kUSD read as 1,000 USD. No row went the other way.
  - 75 of 309 rows in WORK/cmp/tables/tolerance_forms.csv: the tolerance has the unit glued to the number or separated by anything other than an ASCII space (`500kUSD`, `500<TAB>kUSD`, non-breaking space, `0.5kUSD`, `500MUSD`).
  - 37 of 145 rows in WORK/cmp/tables/inline_units.csv: a value cell carries its own unit and the unit cell is empty (`30 kUSD` with an empty `reference_unit`).
  - 3 rows in the random tables.
- Minimal reproduction, WORK/repro/kusd.csv (5 rows):
  - NEW `check`: "decided: 3 of 5", 3 lenient (rows `glued`, `tab`, `inline`), 2 undecided.
  - OLD `grader-check`: "decided: 0 of 5", 5 undecided.
- Cause: src/consilience_judge_check/grader.py lines 236-238. The tolerance's unit is examined only if the tolerance contains an ASCII space (`tol.split(None, 1)[1] if " " in tol else ""`), and a unit written inside a value cell is never examined. The pinned engine has no such rule, so after this package is imported the engine's `compare` reads `kUSD` as 1,000 USD (OLD: `unparseable`).
- Not caught by the tests: tests/test_grader.py lines 157-178 cover only the three ordinary positions with a space-separated tolerance.
- Not affected: the study. Its four tables are all same-unit and identical old vs new. The tool's own `table` command always writes "number, one space, unit".
- In the three ordinary unit positions (`reference_unit`, `stated_unit`, `tolerance` as "10 kUSD"), OLD and NEW agree on decided or undecided for all 158 unit spellings I tried, in 6 row shapes each (948 rows). That includes `USD/year`, `USD**2`, `mUSD`, `MUSD`, `usd`, `US$`, and a tolerance in another currency.

2. For prefixed-currency rows the `undecided` entries differ in text, so a pre-move receipt for such a table does not verify with the new tool.

- 2,109 rows are undecided in both but with different entries. Examples:
  - Reference or stated position: detail was `unparseable(a.unit: unknown_unit)`, now "a currency code takes no prefix: write the full amount (USD, not kUSD)".
  - Tolerance position: reason was `unusable_input(--abs-tol '10 kUSD': unknown_unit: 'kUSD' ('USD' takes no prefix ...))`, now `unparseable`.
  - A row with a second defect (for example an empty stated value): reason was `not_stated`, now `unparseable`.
- Consequence: OLD wrote a receipt for a two-row table with kUSD only in the ordinary positions (WORK/repro/kusd_std.csv). NEW `verify` on it prints "FAILED ... BAD re-run: the re-run gives a different result". CHANGELOG.md line 21 ("Receipts written before the move ... still verify") holds for the study's six receipts, not in general.
- Smaller, same lines: the new detail text always says "(USD, not kUSD)" whatever the unit was (kEUR, MJPY). grader.py lines 311-312.
- You told me the only intended difference was the extra `judge_check_version` field. Findings 1 and 2 are differences beyond that.

3. PROVENANCE.md lines 10 and 11 give the two source hashes swapped.

- What I ran: `sha256sum` on the files in the dataset folder.
- Expected: `test.jsonl` sha256 `ad0f944f6a8a…` and TeX sha256 `e35bfe78cd82…`.
- What happened: `test.jsonl` hashes to e35bfe78cd82…; `draco_paper.tex` hashes to ad0f944f6a8a….
- That `test.jsonl` is the file the study used: the adapter turns it into a rubric.csv with sha256 18262c75…, 800,123 bytes, exactly what contracts.json records.
- The same swap is in studies/judge-check-2026/PREREGISTRATION_DRACO.md lines 13-14 (kept as written).
- A reader checking their dataset copy against PROVENANCE will see a mismatch.

4. Two commands in the README's front table fail as written.

- README.md line 14, `consilience-judge-check probes contracts.json`: exit 2, "the following arguments are required: --out".
- README.md line 15, `consilience-judge-check table probes.csv verdicts.csv`: same.
- Exit 2 is also not among the documented exit codes (cli.py line 11: "Every command: 64 for an input that cannot be used").
- The same commands with `--out` in docs/rubric.md and the study README work.

5. The four `check` receipts verify only when run from the repository root.

- Their recorded table path is root-relative (`studies/judge-check-2026/results/...`).
- From inside `studies/judge-check-2026`, or from `/` with an absolute path, `verify` exits 64: "the data file named in the receipt ... was not found; pass its location with --data". The probes receipt and the engine receipt verify from anywhere.
- `python -m pytest <repo>` run from another directory gives 2 failed, 195 passed (`test_the_published_study_receipts_still_verify`, `test_the_published_study_comes_out_of_the_product_alone`).
- The READMEs do tell the reader to be in the repository root, and there everything passes.

6. Claims that are overstated, imprecise, or that I could not confirm.

- README.md line 88, "The 197 tests include the hostile criteria written by the auditors": the tests hold 119 hostile strings. Of the 766 distinct criteria in the three auditor files, 117 appear in the tests (106 as must-be-left-out, 11 as read-right).
- README.md line 94, the verify command "confirms 2,872 right, 139 lenient and 40 strict": `verify` prints only ok lines and a hash, no counts. The counts are right; I got them from `check` on the table.
- CHANGELOG.md line 34, test sentences rebuilt "Byte for byte the same (sha256 147522f41376131e…)": true through `verify`, the tests and the Python keyword `comment=PROBES_COMMENT_AS_FIRST_WRITTEN`. The `probes` command with the receipt's offsets writes sha256 2c08b5bb9c64…, differing in line 1. There is no command-line way to produce the stored file. The stored tables are the same case (identical after line 1).
- PROVENANCE.md line 10, "Nothing else from the dataset is stored":
  - items.json and contracts.json also hold the task id, criterion id, weight, domain and section of the 76 criteria.
  - AUDIT_PRODUCT.md lines 276-277 quote two further DRACO criterion texts verbatim.
  - No task problem text is stored, and the grading prompt is not stored beyond a one-sentence quote.
- PROVENANCE.md line 18, "holds one function, `tested_range`" from earlier work: adapters/discoverphysics.py also holds `class ExecutorLaw` (line 71), `world_variance`, `noise_sigma`, `test_cases`, `trajectory_score` and `benchmark_commit`. The study's scripts call only `_import` (pilot/judge_arm.py line 157, pilot/with_usage.py line 16). Its docstring (line 7) lists a `reference_law` that is not in the file.
- Study README line 350, "4,464 judge calls with a verdict": the call files hold 4,469 records, 10 with an error (5 second-judge, 5 smaller-judge), so 4,459 without. This line was not changed by the move.
- Study README line 354: the move changed the cost from "About 32" to "About 34" US dollars. Only the second judge's spend is stored (2.9994 USD), so I could confirm neither figure.
- README.md line 119 says the study was run on 20 and 21 Nov; study README line 352 says "Run on 20 Nov 2026". The call records carry no dates. The old branch has a study commit on each day.
- Could not confirm:
  - that each preregistration was committed before its run. The old repository adds each in the same commit as, or after, its results; the READMEs say the order is in a private repository.
  - the "as committed" hashes of three preregistrations. The published DRACO, DRACO replication and DRACO second-judge files hash to 847d1e88…, 9f46b3bf… and 2d0dac02…, not the listed values, as the README says they would. The other three match (1f9e5608…, 5243c60d…, f1b59a5d…).
  - that nothing is copied from DiscoverPhysics. I did not have that repository.

7. Smaller mismatches between documents and tool.

- docs/check.md lines 89-96: the example output is shown as if complete. The tool prints 13 lines (also `data:`, two `group` lines, `could not decide`, `result`, `receipt`, `wrote`), and each disagreement line ends with "row receipt <12 hex>". docs/rubric.md says its output is shortened; check.md does not.
- docs/rubric.md lines 75-79: the review.csv listing shows 2 rows; the tool writes 4 (r1, r2, r3, r6). The cut is not marked.
- docs/rubric.md line 71 says "two audits each found text it misread"; line 248 and the README say three.
- docs/rubric.md line 197, "add others with `--lead`": `--lead Reports` replaces the default. A "States ..." criterion is then left out as `does_not_start_with_a_lead_word`; you need `--lead States --lead Reports`. Same in OLD.
- `verify --help` says "a contracts file, a probes receipt or a check receipt"; it also accepts the engine's receipts, which the study README relies on.
- `verify contracts.json` with the rubric absent prints FAILED and exits 1; a `check` receipt with its table absent is an error, exit 64.
- Study README lines 262-265: `probes contracts.json --out probes.csv` with default offsets writes 759 probes at a different set of distances from the stored 856-probe file that the next sentence points to.
- Study README line 23 (note on names) lists preregistrations, `pilot/` and audit records; the two files under `adapters/` also use the old names. PROVENANCE.md line 16 does list them.

8. Receipts: what `verify` does not check (observation; the documents do not promise more).

- A receipt with a wrong, null, added or removed `judge_check_version` verifies as ok, provided its `sha256` was recomputed. Without recomputing it fails on "receipt hash". Same for `consilience_version` and `pint_version`. grader.py lines 400-414 restamp these on purpose.
- Other fields that survive an edit plus a recomputed hash: `command` in contracts and probes receipts, `inputs.rubric.bytes` in a contracts file, and `inputs.data.path` in a check receipt when `--data` is given.
- Old/new differences at the edges of `verify`:
  - a check receipt stamped `consilience_version: "0.1.0"`, or with that field removed: ok in NEW, FAILED in OLD.
  - a receipt written by NEW: FAILED with the old `consilience verify` for check and probes receipts; a contracts file still passes.

9. Cleanliness.

- Secrets or keys: none. Absolute machine paths: none. E-mail addresses: none.
- Model names in prose:
  - AUDIT_PRODUCT.md line 24 says "the [family] preregistration".
  - The family name is in three path names (`PREREGISTRATION_DRACO_[FAMILY].md`, `pilot/draco_[family].py`, `results/draco_[family]/`), which the study README prints at lines 308 and 333.
  - Study README line 345 says "The text of this study does not name models".
  - Outside the raw call records, exact model identifiers are in results/draco_contracts/summary.json line 209, results/draco_replication/summary.json line 168 and results/draco_[family]/run_summary.json line 4.
- Not in a tracked file, but public: the commit's author is [the AI assistant's name and address] and its message names a specific model in a Co-Authored-By line and carries a session link. The prose says only "an AI coding assistant".
- Carried over from other work: LICENSE-DATA line 5 speaks of "rule packs, vocabularies", which this repository does not have (the file is byte-identical to the old repository's). adapters/discoverphysics.py is covered in finding 6 (it imports `consilience_laws` at line 134).
- Leftover references to missing paths (`docs/grader-check.md`, `src/consilience/`, `consilience.rubric`): only inside AUDIT_PRODUCT.md, which is intended.
- Old command names outside preregistrations, `pilot/`, `adapters/`, audit records and result files: only in explanatory places (CHANGELOG mapping table, the note on names, docs/check.md line 167, the two `*_AS_FIRST_WRITTEN` constants, receipt `command` values). None tells a reader to type an old command.
- Organisations: only Perplexity, plus provider library names inside pilot scripts.

### CHECKED AND FOUND CORRECT

Install and tests
- `pip install --no-cache-dir -e ".[test]"` in a fresh venv worked. pip cloned github.com/Anuja-Khatri/consilience-core and resolved it to b5fa2ef168370815bb3d523cccb27730605671c6 (consilience 0.2.0.dev0).
- The 33 installed engine files are byte-identical to that commit's `src/consilience`. That commit is the tip of `pooling-check` on GitHub and an ancestor of the old `grader-check` branch.
- `python -m pytest`: 197 passed, 0 failed, on Python 3.13.18, 3.11.18 and 3.10.20, and with pint 0.23. The old versions of the two test files also give 197 passed on the old code.
- The public repository changed while I worked:
  - at 15:29 UTC it was public but empty; `git clone` gave an empty repository and the README's `pip install "git+https://..."` failed.
  - at 15:55 UTC its `main` was bfb7d65, the same tree as the clone I was given.
  - I then followed the README from GitHub: clone, install, 197 passed, the five `verify` commands ok, and the `pip install git+https` form worked.
- One limit: my session reaches GitHub through a proxy, and the API would not show consilience-core's visibility, so I cannot prove it is readable with no credentials. The clone needed no access request.

Documents against tool
- docs/rubric.md worked example: scan output, the four probe sentences, the check output lines and the Python snippet all match. `+1.1u` gives "$31,350 million" and the default offsets are as stated.
- docs/check.md example: counts and both disagreement lines match; exit codes 0, 1, 3 and 64 are as documented; "nothing was checked" for a header-only table; `--data` works.
- All six `--help` outputs run.
- The study README's adapter, scan, probes, table and check commands run.
- Four no-model scripts reproduce the stored files byte for byte: `draco_replication.py summarise`, `draco_robustness.py`, `draco_grader_table.py` and `draco_[family].py verdicts`. So does `adapters/draco_saved_verdicts.py` (3,051 verdicts).

Old against new
- `read_criterion`: 14,163 calls, 0 differences. That is 103 + 414 + 250 hostile criteria, 20 from a fourth auditor file, and 3,934 DRACO criteria, each raw, stripped and with extra lead words.
- `scan_rubric` on DRACO with the section filter: `result` identical (3,934 read, 207 mention a tolerance, 76 accepted). The scan output is byte-identical to the stored review.csv.
- `build_probes` with the receipt's offsets: 856 rows identical, text identical after line 1. NEW with `PROBES_COMMENT_AS_FIRST_WRITTEN` equals the stored probes.csv, sha256 147522f41376131e….
- `build_probes` and `probe_table` on 111 odd inputs: identical, including error messages.
- `probe_table` on both stored verdict files: identical after line 1; with the earlier comment, byte-identical to the stored tables.
- `check_grader`:
  - the four study tables: identical `summary`, `disagreements` and `undecided`, and the receipt differs only by `judge_check_version` (2,298: 2,218 / 57 / 23; 753: 654 / 82 / 17; 3,051: 2,872 / 139 / 40; 473: 473 / 0 / 0).
  - the two worked-example tables and 22 of my 34 readable edge-case tables: fully identical.
  - 11 unusable files: the same error in both.
  - the 12 edge-case tables that differ: every differing row has a prefixed currency (findings 1 and 2).
- Printed reports: NEW output equals the stored `grader_check*.txt` except the receipt hash line and the `wrote:` line.

Receipts
- All 7 receipt files under `studies/` verify: 4 check receipts, the probes receipt and the engine receipt from the repository root; contracts.json with `--data` pointing at the rebuilt rubric.
- Tampering is caught:
  - one byte of a table changed, CRLF conversion, or an appended newline: FAILED on data hash.
  - a number edited in a receipt: FAILED on receipt hash, and FAILED on re-run when the hash is recomputed.
  - 1,275 single-field edits across 7 receipts: every one fails without a recomputed hash. With a recomputed hash only the fields listed in finding 8 pass.
  - one byte of probes.csv or rubric.csv changed: FAILED.
  - a hand-edited contracts file builds no probes, even with its hash recomputed.

Claims
- Study folder: 66 files; 65 byte-identical to the old branch; only README.md differs.
- Six preregistrations; four audits (one in AUDIT.md, three in AUDIT_PRODUCT.md).
- The test of 849 stored responses exists and passes.
- The six receipts re-run unchanged.
- Spot checks of study numbers against the stored tables hold: 27 of 76, 10 and 22, 14 of 69 against 0 of 69, ten tasks with 39 in the largest, 15 and 78 of 565, 0 and 4 of 38, 5 of 5.

### NOT DONE

- Nothing was run against the DiscoverPhysics repository, and no script that makes a model call was run.
- The study's result tables were spot-checked, not re-derived line by line.
- I did not write new hostile criteria for the reader; I tested old-against-new equality, not the reader's correctness.
- Python 3.12, Windows and macOS were not tried.
- An attempt to read the proxy notes and environment variables was denied by the permission system; I did not pursue it.
