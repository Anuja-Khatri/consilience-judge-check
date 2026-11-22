# Provenance

Where each thing in this repository came from.

| What | From | Commit or version | How |
|---|---|---|---|
| `src/consilience_judge_check/rubric.py`, `grader.py`, the command line, `tests/`, `docs/` | This project's own `consilience` package, on a working branch that was not published | 20 and 21 Nov 2026 | Moved here on 21 Nov 2026. `CHANGELOG.md` lists what changed in the move and how it was checked |
| The Consilience engine: `compare`, unit reading, the table reader, hashing, the engine's own `verify` | [Anuja-Khatri/consilience-core](https://github.com/Anuja-Khatri/consilience-core) (MIT), branch `pooling-check` | commit `b5fa2ef168370815bb3d523cccb27730605671c6` (0.2.0.dev0) | Installed as a dependency. Nothing is copied |
| The reading rules and the sentence builder in `rubric.py` | This project's own study script `studies/judge-check-2026/pilot/draco_contracts.py` (20 Nov 2026) | | Moved into the tool and rewritten in exact decimal arithmetic. A test rebuilds the study's 849 stored responses byte for byte |
| Criterion texts in `studies/judge-check-2026/results/draco_contracts/items.json` and in the files built from them | The DRACO dataset, `perplexity-ai/draco` on Hugging Face (MIT), `test.jsonl` sha256 `e35bfe78cd82…` | read 20 Nov 2026 | 76 criterion texts copied and credited, with each one's task id, criterion id, weight, domain and section. `AUDIT_PRODUCT.md` quotes two further criterion texts. No task text is stored |
| The DRACO grading prompt | The DRACO paper, arXiv 2602.11685, appendix | TeX sha256 `ad0f944f6a8a…` | Read from the paper at run time. Not stored here, beyond one sentence quoted in the write-up |
| The DiscoverPhysics judge, rubrics and reference explanations | [SampsonML/DiscoverPhysics](https://github.com/SampsonML/DiscoverPhysics) (MIT) | `33b7fa9df96d` | Imported and called at run time. Nothing copied |
| The judge call records, tables and receipts in the study folder | Produced for this study on 20 and 21 Nov 2026 | | Every call kept. The scripts that made them are in the study's `pilot/` folder |
| `studies/judge-check-2026/AUDIT.md`, `AUDIT_PRODUCT.md` | Four independent audits by separate AI sessions, 20 Nov 2026 | | Each report is kept as returned, with what was changed for each finding |
| `AUDIT_MOVE.md` | An independent check of this repository after the move, by a separate AI session, 21 Nov 2026 | | Kept as returned, with what was done about each finding |
| `studies/judge-check-2026/AUDIT_REASONING.md` | An independent recount of the reasoning experiment, by a separate AI session, 21 Nov 2026 | | Kept as returned, with what was done about each finding |
| `studies/judge-check-2026/AUDIT_SECOND_JUDGE.md` | An independent recount of the run on the second judge, by a separate AI session, 22 Nov 2026 | | Kept as returned, with what was done about each finding |
| `studies/judge-check-2026/PREREGISTRATION_DRACO_REASONING.md`, `pilot/draco_reasoning.py`, `results/draco_reasoning/` | Written and run for this study on 21 Nov 2026, after the move | | One sentence naming who approved the spending was removed from the preregistration for publication. One comment in the script was corrected after the run and says so |

**Kept as written, with three exceptions.** The preregistrations, the scripts in `pilot/` and `adapters/`, the audit records and the result files in the study folder are as they were on the working branch, and name the commands as they were called then (`consilience rubric scan`, `consilience grader-check`). The exceptions:

- The study's `README.md` was edited for the move.
- Three paths carried the name of the second judge's model family and were renamed: `PREREGISTRATION_DRACO_SECOND_JUDGE.md`, `pilot/draco_second_judge.py`, `results/draco_second_judge/`. The paths written inside those two files were changed to match, one word in `AUDIT_PRODUCT.md` was changed for the same reason, and the receipt and printed report in that results folder were written again because they record the table's path.
- Nothing else.

**Two hashes the wrong way round.** `PREREGISTRATION_DRACO.md` gives the dataset's hash and the paper source's hash swapped. The table above has them the right way round. The preregistration is left as it was written.

**One loose end.** `studies/judge-check-2026/adapters/discoverphysics.py` was written for an earlier and closed piece of work and holds more than this study uses: `ExecutorLaw`, `world_variance`, `noise_sigma`, `test_cases`, `trajectory_score`, `tested_range` and `benchmark_commit`. The study's scripts call only `_import`. `tested_range` needs a package that is not in this repository, and the file's opening comment lists a `reference_law` that is not in it.

**How it was written.** The code and text were written with an AI coding assistant under the project owner's direction. What was written down before each run is in the study folder. The commit history that shows the order is in the owner's private working repository.
