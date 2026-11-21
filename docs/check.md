# check: where the right answer is arithmetic, is the grader right?

## The problem

More and more work is scored by a rubric and a grader: research reports graded by a
language-model judge, benchmark answers marked criterion by criterion, model outputs
scored to produce a training reward. Most of what a rubric asks needs judgement. Some of
it does not. A criterion such as "states the revenue as 30.8 billion dollars (within 0.5
billion)" has exactly one right verdict, and it is fixed by arithmetic.

On those criteria a grader can still be wrong, and the usual ways of checking a grader do
not show it:

- **Running the grader several times** shows whether it is consistent. A grader can be
  consistently wrong.
- **Comparing several graders** shows whether they agree. It does not show which is right.
- **Human labels** show which is right, but they are slow and costly, and for these
  criteria nobody needs to be asked.

`check` uses the one thing those criteria offer: the answer is known without
asking anyone. It takes cases a grader has already graded, decides each one by
arithmetic, and reports where the grader differs.

The arithmetic is simple, and anyone could do it by hand for one criterion. What the
command adds is doing it the same way every time: exact decimal arithmetic, units read
and checked, a case left undecided when it cannot be decided exactly, counts by criterion
and not by call, and a receipt that anyone can re-run. It checks a grader. It does not
discover anything about the work being graded.

## Who it is for

| You are | What it gives you |
|---|---|
| The authors of a benchmark scored by a judge | An error rate for your judge on the criteria that have a known answer, with no human labelling. A check to run again whenever the judge model changes or is retired |
| Training a model on rubric rewards | The part of the reward that can be computed by rule instead of graded, and how often the graded version would have paid for a wrong answer |
| Choosing between judge models | A like-for-like count of lenient and strict errors for each, on the same cases |
| Reviewing or reproducing a judged result | A receipt that re-runs: this table, these rows where the verdict differs from the arithmetic |
| Running any grading at scale (people or scripts) | The same check. Nothing in it assumes the grader is a model |

## What you need, and what you get

You need a table with one row per graded case: the value the rubric names, its
tolerance, the value the response stated, and the verdict the grader gave. You get, per
row, one of four outcomes:

| Outcome | Meaning |
|---|---|
| right | The grader's verdict is the verdict the tolerance fixes |
| lenient | The grader accepted a value outside the stated tolerance |
| strict | The grader rejected a value inside the stated tolerance |
| could not decide | The Consilience engine refused the row (a unit it cannot read, two kinds of quantity, no tolerance) or the grader's verdict could not be read. Reported with the reason; never guessed |

and a count of each, overall and by any group you label (for example, how far the stated
value was from the edge of the tolerance). **The grader is never run by this command.**
The table holds verdicts it already gave, so the tool needs no model, no key and no
network.

A first study that used it, on two public benchmarks, is in
[studies/judge-check-2026](../studies/judge-check-2026/README.md).

## The table

A CSV file with a header row. Lines starting with `#` before the header are ignored.

| Column | What |
|---|---|
| `id` | Any label for the row |
| `reference_value` | The value the rubric names |
| `reference_unit` | Its unit, for example `USD`, `percent`, `count`, `mV` |
| `tolerance` | The stated tolerance, a quantity such as `500000000 USD`. A bare number is in the reference unit |
| `stated_value` | The value in the graded response |
| `stated_unit` | Its unit. It may differ from the reference unit if the two convert (`mV` and `V`) |
| `grader_verdict` | `met` or `unmet` (also pass/fail, yes/no, true/false, 1/0) |
| `group` | Optional. A label to count by |

A made-up example:

```
id,reference_value,reference_unit,tolerance,stated_value,stated_unit,grader_verdict,group
a1,30800000000,USD,500000000 USD,31050000000,USD,met,inside
a2,64000000,USD,2000000 USD,66200000,USD,met,outside
a3,19.67,USD,0.50 USD,20.12,USD,unmet,inside
```

```bash
consilience-judge-check check cases.csv --receipt receipt.json
```

```
decided:     3 of 3 (3 in exact decimal arithmetic, 0 after a unit conversion)
grader right: 1
lenient:     1 (accepted a value outside the stated tolerance)
strict:      1 (rejected a value inside the stated tolerance)
  line 3    a2  outside  lenient: stated 66200000 USD, reference 64000000 USD, tolerance 2000000 USD, difference 2.2e+06 USD
  line 4    a3  inside  strict: stated 20.12 USD, reference 19.67 USD, tolerance 0.50 USD, difference 0.45 USD
```

(The output is shortened here. The tool also prints the table's hash, a count for each
group, the rows it could not decide, the result and the receipt's hash, and each
disagreement line ends with a short receipt for that row.)

Exit codes: 0 the grader is right on every row, 1 it differs on some, 3 some rows could
not be decided, 64 the table itself is unusable, 2 the command line cannot be read.

```bash
consilience-judge-check verify receipt.json
```

re-reads the table, re-runs every comparison and confirms the receipt
(`consilience-grader-receipt/v1`). Pass `--data` if the table has moved.

In Python:

```python
from consilience_judge_check import check_grader
g = check_grader("cases.csv")
g.summary, g.disagreements, g.undecided, g.receipt
```

## Counting items, clusters and rounding

Three more columns are optional. They are written for you by `consilience-judge-check table`
(see [rubric.md](rubric.md)), and can be added to any table by hand.

| Column | Meaning | What the report adds |
|---|---|---|
| `item` | What the row is a case of, for example the criterion | Counts of items: an item is wrong if any of its rows is. A 95% interval at the item level |
| `cluster` | A label for items that belong together, for example the task | How many clusters hold a wrong item; the largest cluster beside all the others |
| `reference_step` | One unit of the last digit the reference is written to (1000000 for "$64M") | For the accepted values: how many are still outside the tolerance after ordinary rounding to that precision, and how many even when rounded toward the reference. Rows where this cannot be worked out (no step, or a unit conversion) are counted as not checked |

A grader called three times on the same case at a near-deterministic setting has not
been tested three times. Count items.

Rows with an empty `item` are counted as rows only. An item named in two clusters is
counted in the first. If several clusters are the largest, the first by name is shown
and the report says so. A table with no rows is reported as "nothing was checked".

## How each row is decided

The Consilience engine's `compare(reference, stated, abs_tol=tolerance, precision="exact")`
is run on every row, so units are read and checked the same way as in the `consilience`
package. A row whose units cannot be read, or are of different kinds, is left undecided.
Then:

| The row | How it is decided | In the receipt |
|---|---|---|
| Reference, stated value and tolerance all in the same unit | Exact decimal arithmetic on the digits as written: inside if the difference is no more than the tolerance | `method: exact` |
| A unit conversion is needed | The engine's floating-point answer | `method: float` |
| A unit conversion is needed and the value is within floating-point noise of the edge (about four parts in a billion of the larger value) | Not decided | `at_the_edge` |

The tolerance the rubric states is the whole tolerance: nothing is added for the number
of digits written. A value exactly on the edge is inside.

Write a table in one unit where you can. Then every row is decided exactly, and the
printed report says so ("2298 in exact decimal arithmetic, 0 after a unit conversion").

Currency amounts use the codes `USD`, `EUR`, `GBP`, `INR` and `JPY`. Each is an amount
of its own kind: dollars are not compared with euros, because an exchange rate is not a
unit conversion, and no prefix is read (`kUSD`). Write amounts in full.

## The receipt

The report is a receipt of the kind `consilience-grader-receipt/v1`. It names the table
by hash, holds every count and every disagreement, and carries its own hash.
`consilience-judge-check verify receipt.json` reads the table again, decides every row
again and confirms the result is the same. It means "re-runs to the same answer". It does
not say who wrote the receipt.

Two fields need a word:

- `command` holds `grader-check`. That is the name this operation has had in the receipt
  format since its first version, when the command was part of the `consilience` package.
  It is kept so that receipts written then still verify unchanged.
- `consilience_version` is the version of the engine that read the units.
  `judge_check_version` is the version of this package. Receipts written before this
  package had its own version number do not carry the second, and still verify.

**What `verify` compares, and what it does not.** It compares the table's bytes and the
result. The version fields are not part of that comparison: a receipt whose version
field was edited and whose hash was then recomputed still verifies, because the same
table gives the same result. A receipt is found from the folder it is in: `verify` looks
for the table at the recorded path and then beside the receipt, and checks it by hash.

## What it does not do

- **It does not run the grader, and it does not show that the grader produced the
  verdicts in the table.** The receipt says: given this table, these are the rows where
  the verdict differs from the arithmetic.
- **It does not read prose.** Someone has to say which value the response stated. For a
  response built to state one value that is trivial; for free text it is the hard part.
- **It covers only criteria whose answer is a comparison under a stated tolerance.**
  Criteria that need judgement are not its business.
