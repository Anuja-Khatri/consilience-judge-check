# Preregistration: DRACO judge, second arm (near the boundary, and in other units)

**Written before any call in this arm, and after the first arm was read.** 20 Nov 2026. Follows `PREREGISTRATION_DRACO.md`. Same dataset, same grading prompt, same judge configuration, same 76 items (`results/draco_contracts/items.json`, sha256 `f8edd2ae1d27…`, unchanged).

## What the first arm showed, and why this arm exists

The judge gave the wrong verdict on 15 of 1,572 calls whose right verdict is known (about 1%). In every one of the errors I read, the judge wrote out the correct allowed range and then compared the stated value with it wrongly, for example "a $50,000 loss, which is within the acceptable range… ($35,000 to $45,000)". The first arm tested values half a tolerance inside and two tolerances outside. This arm asks whether the slips become more common in two harder and more realistic cases: a value close to the edge of the tolerance, and a value written in a different unit from the criterion's. Because this arm was designed after seeing the first, it is a follow-up and is labelled as one wherever it is reported.

## Conditions

Responses are built by rule from the same claims (`pilot/draco_contracts.py boundary-items`, written to `results/draco_contracts/items_boundary.json`, sha256 `847c8680219e…`). The expected verdict of each was checked by separate arithmetic (0 problems in 248 responses).

| Condition | The number stated | Right verdict | Items |
|---|---|---|---|
| near, inside | value plus 0.9 of the tolerance | MET | 76 |
| near, outside | value plus 1.1 of the tolerance | UNMET | 76 |
| other unit, inside | the same inside value, written in another unit ("$16,273 thousand" as "$16.273 million") | MET | 48 |
| other unit, outside | the same outside value, written in another unit | UNMET | 48 |

- The other-unit conditions apply to money criteria only, and only where the value can be written in another of dollars, thousand, million or billion as a number between 1 and a million. 48 of the 58 money items qualify.
- Bare sentences only. Three calls each. 744 calls.

## Outcomes

| # | Outcome |
|---|---|
| B1 | Wrong-verdict rate per condition, by call and by item, with a 95% interval |
| B2 | The same-unit rates here (0.9 and 1.1 tolerances) beside the first arm's (0.5 and 2 tolerances) |
| B3 | The other-unit rates beside the same-unit rates, on the 48 items that have both |
| B4 | Items whose three identical calls disagree |

## Expectations, stated so they can be wrong

- Near the boundary I expect more errors than the first arm's 1 to 3%, but I do not know how many more. My guess is between 2% and 10%.
- I expect the other-unit conditions to be worse than the same-unit ones, because a conversion comes before the comparison.
- If the rates are no higher than the first arm's, that is reported as it is: the judge's arithmetic does not get worse at the edge or across units.

## Limits

The same as the first arm: one judge of three and not the paper's primary one; single sentences; 76 Finance-heavy criteria from 10 tasks. A response that states a figure to more decimal places than a real report would is a test of arithmetic, not of typical reports.

Cost: about 3 US dollars.
