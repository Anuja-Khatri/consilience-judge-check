# Preregistration: DRACO known-answer test on a judge from the primary judge family

**Written and committed before any call of this run.** 20 Nov 2026. Follows the three earlier DRACO preregistrations. Same dataset, same grading prompt, same 76 criteria.

## Why this run exists

Every DRACO result so far is on the third of the three judges the paper reports. The paper's primary judge was not tested. [One sentence naming a person removed for publication. The file as committed before the run has sha256 54499db287af0a98….] A key for that provider and a budget of 5 US dollars were available.

**The paper's primary judge cannot be tested by anyone.** Its provider has shut the model down: on 20 Nov 2026 the provider's model list no longer offers it. This run uses **its direct successor in the same model line**, at the settings the paper gives for the primary judge (thinking level low, temperature 0.2). So this is not a test of the paper's primary judge. It is a test of the judge that someone running DRACO today with that family would have to use. Every write-up will say so.

## The cases come from the product

This is the first run whose cases are built by the Consilience package itself, not by a script of this study.

| Step | Command | Result |
|---|---|---|
| Find the checkable criteria | `consilience rubric scan` on DRACO's rubric | 76 of 3,934 criteria (contracts file sha256 `6c8d25012b88…`) |
| Build the cases | `consilience rubric probes` | `results/draco_product/probes.csv`, sha256 `147522f41376…` |

For every distance used in the earlier arms the product's text is the same, byte for byte, as the text the first judge was sent (849 stored responses compared, 0 differ).

## Harness

- Grading prompt: the one printed in the DRACO paper, byte for byte, as system message; the paper's user template.
- The provider's chat endpoint that accepts a bearer key, with `temperature` 0.2 and `reasoning_effort` low. Output limit 2,048 tokens.
- The verdict is read by rule from the status field of the reply.
- A call that fails or has no readable status is recorded and counted, never dropped.

**Two calls were made before this file was written**, on probes that are not part of the run (3 tolerances outside), to learn the reply format and the cost of a call. Both were answered UNMET, which is right. They cost half a cent each. They are kept in `results/draco_gemini/pings.jsonl` and are not part of any result below.

## Stages, in fixed order

One call per criterion unless stated. The order is fixed here and will not change.

| Stage | The number stated | Right verdict | Calls | Estimated cost |
|---|---|---|---|---|
| 1 | 1.1 tolerances below, and 1.1 above | UNMET | 152 | 0.8 |
| 2 | The criterion's own value (MET), and far off (UNMET) | controls | 152 | 0.8 |
| 3 | 1.1 above, inside the long report used before (69 criteria) | UNMET | 69 | 0.8 |
| 4 | 0.9 below, and 0.9 above | MET | 152 | 0.8 |
| 5 | Stage 1 again, twice more | UNMET | 304 | 1.6 |

**Stopping rule.** Spend is metered from the token counts the service returns, at 2 US dollars per million input tokens and 12 per million output tokens (thinking included). No new call starts once the metered spend reaches **4.25 US dollars**. A stage cut short is reported as incomplete, with the criteria it reached (they are taken in order of id). No stage is dropped, added or re-ordered after results are seen.

## Outcomes and rules, fixed now

The unit is the criterion. A criterion counts as wrong if any of its calls gives the wrong verdict.

| # | Question | Rule fixed in advance |
|---|---|---|
| G1 (primary) | Does this judge accept a value 1.1 tolerances below the reference? | **Shared** by this judge if it says MET on at least 4 of 76 criteria. **Not shown** if 3 or fewer. The same rule as the replication arm |
| G2 | The same, 1.1 above | Same threshold, reported beside G1 |
| G3 | Controls: does it accept the exact value and refuse a far-off one? | If more than 3 of 76 are wrong on either control, the harness is suspect and nothing here is read as being about the judge |
| G4 | Inside a long report | Shown at 4 or more of 69 |
| G5 | Does it refuse a value just inside? | Reported as counted |
| G6 | Do repeated calls agree? | From stage 5, as far as it gets |
| G7 | Failed or unreadable calls | If more than 5% of a stage's calls have no verdict, that stage is called unreliable |

## Expectation, stated so it can be wrong

I do not know. This judge reasons before it answers, which should help with a comparison of two numbers. My guess is **0 to 6 of 76 criteria** at 1.1 below, and I think "not shown" is more likely than "shared".

## What the write-ups will say, by outcome

| Outcome | What is said |
|---|---|
| Shared (G1 at 4 or more) | The behaviour is seen on two judges from two providers, including the current judge of the primary family |
| Not shown (G1 at 3 or fewer) | The finding is stated as specific to the paper's third judge. The write-up says plainly that the current judge of the primary family did not show it. That is good news for the benchmark and is reported as such. The tool's use is then "it tells you which judge can be trusted on these criteria" |
| Controls fail (G3) | No conclusion about the judge; the harness is examined and the run reported as failed |

## Limits

- The successor model, not the paper's primary judge.
- One call per criterion in stages 1 to 4.
- The same 76 criteria from 10 tasks, mostly Finance, one task holding 39 of them.
- This study's harness, not DRACO's. In particular the endpoint used may not be the one DRACO's authors used.
- Built sentences, not real system reports.
