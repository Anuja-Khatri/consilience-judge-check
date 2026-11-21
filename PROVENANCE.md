# Provenance

Where each thing in this repository came from.

| What | From | Commit or version | How |
|---|---|---|---|
| `src/consilience_judge_check/rubric.py`, `grader.py`, the command line, `tests/`, `docs/` | This project's own `consilience` package, on a working branch that was not published | 20 and 21 Nov 2026 | Moved here on 21 Nov 2026. `CHANGELOG.md` lists what changed in the move and how it was checked |
| The Consilience engine: `compare`, unit reading, the table reader, hashing, the engine's own `verify` | [Anuja-Khatri/consilience-core](https://github.com/Anuja-Khatri/consilience-core) (MIT), branch `pooling-check` | commit `b5fa2ef168370815bb3d523cccb27730605671c6` (0.2.0.dev0) | Installed as a dependency. Nothing is copied |
| The reading rules and the sentence builder in `rubric.py` | This project's own study script `studies/judge-check-2026/pilot/draco_contracts.py` (20 Nov 2026) | | Moved into the tool and rewritten in exact decimal arithmetic. A test rebuilds the study's 849 stored responses byte for byte |
| Criterion texts in `studies/judge-check-2026/results/draco_contracts/items.json` and in the files built from them | The DRACO dataset, `perplexity-ai/draco` on Hugging Face (MIT), `test.jsonl` sha256 `ad0f944f6a8a…` | read 20 Nov 2026 | 76 criterion texts copied and credited. Nothing else from the dataset is stored |
| The DRACO grading prompt | The DRACO paper, arXiv 2602.11685, appendix | TeX sha256 `e35bfe78cd82…` | Read from the paper at run time. Not stored here |
| The DiscoverPhysics judge, rubrics and reference explanations | [SampsonML/DiscoverPhysics](https://github.com/SampsonML/DiscoverPhysics) (MIT) | `33b7fa9df96d` | Imported and called at run time. Nothing copied |
| The judge call records, tables and receipts in the study folder | Produced for this study on 20 and 21 Nov 2026 | | Every call kept. The scripts that made them are in the study's `pilot/` folder |
| `studies/judge-check-2026/AUDIT.md`, `AUDIT_PRODUCT.md` | Four independent audits by separate AI sessions, 20 Nov 2026 | | Each report is kept as returned, with what was changed for each finding |

**Kept as written.** The preregistrations, the scripts in `pilot/` and `adapters/`, the audit records and every result file in the study folder are byte for byte as they were on the working branch. They name the commands as they were called then (`consilience rubric scan`, `consilience grader-check`). Only the study's `README.md` was edited for the move.

**One loose end.** `studies/judge-check-2026/adapters/discoverphysics.py` also holds one function, `tested_range`, from an earlier and closed piece of work. This study does not use it, and it needs a package that is not in this repository.

**How it was written.** The code and text were written with an AI coding assistant under the project owner's direction. What was written down before each run is in the study folder. The commit history that shows the order is in the owner's private working repository.
