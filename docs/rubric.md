# scan, probes, table: find what arithmetic can check in a rubric, and test a grader on it

## The problem

A rubric is a list of criteria that a grader marks MET or UNMET. The grader is often a
language model, and its marks become a benchmark score or a training reward. Most
criteria need judgement. Some do not:

```
States Q3 revenue as $30.8B (within +/- $0.5B)
```

For a criterion like this the right verdict is a comparison of two numbers. Three
questions follow, and none of them needs a human label or a second model:

1. **How much of this rubric is like that?** Which criteria, and how much of the weight?
2. **Does my grader get those right?** Especially near the edge of the tolerance.
3. **Is it this grader, or the one I am about to switch to?** Models used as graders are
   retired and replaced; the same test can be run again on each.

`consilience-judge-check` answers the first and builds the test for the second and third.
`consilience-judge-check check` then decides every case. **Nothing here runs a grader or a
model.** You run your grader on the cases, in your own harness, and hand back its verdicts.

## Who it is for

| You are | What you get |
|---|---|
| The authors of a benchmark scored by a judge | A count of the criteria that could be scored by rule, and an error rate for your judge on test cases built from them, with nothing to label |
| Training a model on rubric rewards | The part of the reward that can be computed, not graded, and a measure of how often your grader accepts a value the rubric rules out |
| Choosing or replacing a judge model | The same cases run on each candidate, counted the same way |
| Reviewing someone else's benchmark | A test you can build from the public rubric alone |

## The four steps

Made-up data throughout.

**1. Scan the rubric.** A CSV file with the columns `id` and `criterion`; `weight` and
`group` are optional.

```
id,group,weight,criterion
r1,report-A,10,States Q3 revenue as $30.8B (within +/- $0.5B)
r2,report-A,5,"States headcount as 12,400 employees (within +/- 200)"
r3,report-A,5,States gross margin as 41.5% (within +/- 0.5 ppts)
r4,report-A,8,States revenue grew approximately 12% (within +/- 1%)
r5,report-A,4,Explains the main drivers of the margin change
r6,report-B,6,States the exam fee as $93 (within +/- $10)
```

```bash
consilience-judge-check scan rubric.csv --out contracts.json --review review.csv
```

```
rubric:             rubric.csv (6 criteria; sha256 …)
contain 'within +/-' or the plus-minus sign: 5 (83.3%), in 2 of 2 groups
checkable by rule:  4, in 2 groups
left out:           1 not read (counted by reason; nothing was guessed)
      1  wording_not_read
weight:             the checkable criteria carry 26 of 38 positive weight (68.4%); in the 2 groups that have one, from 62.5% to 100.0% of the group's weight
```

(The last lines of the output are left off here.) `r4` is left out because of
"approximately". The contracts file holds each checkable criterion with its value and
tolerance as exact decimals. It is a receipt: `consilience-judge-check verify contracts.json`
re-reads the rubric and confirms it.

**Read `review.csv` before you go on.** It lists every criterion that was accepted, with
the value, tolerance and unit that were read. The reader is careful, but it reads free
text with rules, and two audits each found text it misread (see Limits). A wrong reading
gives a wrong "right verdict" for every probe built from it. Checking the list is quick
and is the real safeguard.

```
id,criterion,value_read,tolerance_read,unit_read,note
r1,States Q3 revenue as $30.8B (within +/- $0.5B),30800000000,500000000,USD,
r2,"States headcount as 12,400 employees (within +/- 200)",12400,200,count,
```

**2. Build the cases.**

```bash
consilience-judge-check probes contracts.json --offsets "+0.9,+1.1,-1.1" --out probes.csv
```

Each probe is the criterion's own claim as one sentence, with only the number changed
to sit at a known distance from the reference, counted in tolerances:

| Probe | Response | Right verdict |
|---|---|---|
| `r1@+0.9` | Q3 revenue was $31.25B. | met |
| `r1@+1.1` | Q3 revenue was $31.35B. | unmet |
| `r1@-1.1` | Q3 revenue was $30.25B. | unmet |
| `r6@-1.1` | The exam fee was $82. | unmet |

Offsets: `0` is the criterion's own value, `+1` is exactly on the edge (inside), `far`
is a clearly wrong value, and a trailing `u` writes a dollar amount in another unit
(`+1.1u` gives "$31,350 million"). The default set is
`0, +0.5, +0.9, +1.1, +2, -0.5, -0.9, -1.1, -2, far`.

**3. Grade them with your grader**, however you normally call it: the probe's
`criterion` and `response` are what it needs. You can also place the response inside a
longer document first. Write the verdicts as a CSV file, one row per call:

```
probe_id,verdict
r1@+1.1,unmet
r2@+1.1,met
r3@+1.1,unmet
r6@+1.1,unmet
r1@-1.1,unmet
r2@-1.1,unmet
r3@-1.1,unmet
r6@-1.1,met
r1@+0.9,met
r2@+0.9,met
r3@+0.9,unmet
r6@+0.9,met
```

Optional columns: `call` (when one probe is graded more than once; give it on every row
of a probe or on none) and `context` (a label such as `report` when the probe was shown
in some setting; such rows are counted as their own group).

**4. Join and check.**

```bash
consilience-judge-check table probes.csv verdicts.csv --out table.csv
```

```bash
consilience-judge-check check table.csv --receipt receipt.json
```

```
decided:     12 of 12 (12 in exact decimal arithmetic, 0 after a unit conversion)
grader right: 9
lenient:     2 (accepted a value outside the stated tolerance)
strict:      1 (rejected a value inside the stated tolerance)
  line 5    r3@+0.9#0  +0.9  strict: stated 41.95 percent, reference 41.5 percent, tolerance 0.5 percent, difference 0.45 percent
  line 8    r2@+1.1#0  +1.1  lenient: stated 12620 count, reference 12400 count, tolerance 200 count, difference 220 count
  line 14   r6@-1.1#0  -1.1  lenient: stated 82 USD, reference 93 USD, tolerance 10 USD, difference 11 USD
by item (an item is wrong if any of its rows is; 95% interval treats items as independent):
  +1.1: 1 of 4 items wrong (5% to 70%), 1 on every row; in 1 of 2 clusters (largest cluster 1 of 3, the others 0 of 1); of 1 accepted, 1 still outside after rounding to the reference's precision, 1 even when rounded toward the reference
```

(The output is shortened here.) The right verdict is not copied into the table:
`check` works it out from the numbers, in exact decimal arithmetic. The table's
`group` column is the probe's distance, kept for counting. See
[check.md](check.md).

In Python:

```python
from pathlib import Path
from consilience_judge_check import scan_rubric, build_probes, probe_table, check_grader

scan = scan_rubric("rubric.csv")
for item in scan.items:                      # read what was accepted
    print(item["id"], item["value"], item["tolerance"], item["unit"], "|", item["criterion"])
rows, skipped, probes_csv = build_probes(scan.receipt, ["+0.9", "+1.1", "-1.1"])
Path("probes.csv").write_text(probes_csv, encoding="utf-8")
# ... grade the probes with your grader and write verdicts.csv ...
table_csv, summary = probe_table("probes.csv", "verdicts.csv")
Path("table.csv").write_text(table_csv, encoding="utf-8")
print(check_grader("table.csv").summary)
```

## What the report counts, and why

Three things in the report exist because the first study that used this tool got them
wrong at first and was corrected by an audit.

- **Items, not rows.** If a grader is called three times on one probe at a
  near-deterministic setting, those are not three trials. The report counts items (an
  item is wrong if any of its rows is) and gives the interval at that level.
- **Clusters.** Criteria from one task are not independent. With a `group` in the
  rubric, the report says how many clusters hold a wrong item, and gives the count in
  the largest cluster beside the count in all the others.
- **Rounding.** A value 1.1 tolerances from the reference can be less than one written
  digit past the edge. For the accepted values the report says how many are still
  outside after ordinary rounding to the precision the criterion was written to, and how
  many are still outside even when rounded toward the reference, which is the reading
  most favourable to the grader. A row where this cannot be worked out is counted as
  "could not be checked", not as inside.

## What is read, and what is not

The reader is an allow-list. **A criterion is used only if it matches a narrow pattern in
full. Anything else is left out and counted under a reason.** Leaving a criterion out is
always safe: it is only not tested.

A criterion is used only if

- it is plain ASCII text of at most 600 characters;
- it starts with a lead word (default `States`; add others with `--lead`) and ends with
  `(within +/- T)`;
- every word in it that holds a digit is recognised in full, either as a date or period
  label (a year, `Q3`, `FY25`, `H1`, `9/30/2025`, `5-year`, a day after a month name) or
  as the one value. A word such as `2.5-year`, `1H24`, `$3.2M-` or `C$9.7M` is not
  recognised, and the criterion is left out;
- the value comes straight after one of a few words: "as", "was", "is", "of", "issued",
  "provided", "suffered". A number anywhere else in the claim ("the Top 1,000
  customers", "Boeing 737") is not guessed at, and the criterion is left out;
- the value is a dollar amount (`$`, with k, thousand, M, million, B, billion), a
  percentage (`%`, pp, ppts, bps) or a count, with or without a word ("705,593 shares",
  "3.24x"), positive, with regular thousands commas and no more than 20 digits;
- the tolerance is the same kind of thing as the value, is read in full, and is smaller
  than the value. If the value has a scale ("$30.8B") the tolerance must have one too.
  If the tolerance carries a word, it must be the word after the value, letter for letter;
- it has no wording this version does not read: hedges ("approximately", "almost"),
  one-sided or negated statements ("at least", "exceeded", "not"), alternatives and
  comparisons ("or", "between", "vs"), a second clause joined by "and", brackets, rates
  ("per", "each"), a sign in words ("negative", "minus"), other currencies, and numbers
  written as words.

| Reason a criterion is left out | Meaning |
|---|---|
| `characters_not_read`, `criterion_too_long` | Not plain ASCII (this includes "±", "€", "–" and unusual spaces), or over 600 characters |
| `does_not_start_with_a_lead_word`, `no_trailing_tolerance` | Not of the form "States … (within +/- T)" |
| `wording_not_read` | Wording from the list above. The list is broad: it also catches harmless uses of "and" or brackets |
| `number_like_tokens_N` | N words look like a value, not one. A period label such as "9M" counts as one |
| `number_not_read` | A word with a digit that is neither a date label nor a value in full, a number that does not follow one of the lead-in words, or a number with irregular commas ("41,5", "0,385") |
| `year_or_value_unclear` | A year-like number follows a lead-in word ("headcount as 2024"), or a bare year or duration label sits beside a bare whole number, so it is not clear which is the value |
| `negative_value`, `value_not_positive` | A minus sign or bracket on the number, or the words "negative" or "minus" |
| `currency_not_read` | A letter before the "$" (C$, HK$, A $), or a currency named in words or by code |
| `scale_letter_without_currency` | "8,849 m", "373 K": without a "$", a letter after a number may be a unit and is not taken for a scale |
| `scale_word_not_read` | "$2.5 trillion", "$120 mln": a magnitude word that is not read |
| `tolerance_not_read`, `tolerance_kind_unclear`, `tolerance_kind_differs`, `tolerance_unit_differs`, `tolerance_scale_unclear` | The tolerance could not be read in full, is another kind of thing than the value, names another unit, or lacks the value's scale. A tolerance given as a percentage of a dollar amount or a count is left out here |
| `tolerance_not_smaller_than_value` | Not a case this version handles |
| `not_selected_or_not_a_positive_criterion` | Excluded by `--where`, or its weight is zero or less (MET means something else there) |

**Two readings are choices, and you should know them.**

- A tolerance written with a percent sign on a percentage, "5.31% (within +/- 0.1%)", is
  read as percentage points, not as a share of the value. The scan says how many
  criteria this applies to, and each is marked in the contracts file and the review list.
- A stated decline or loss ("a decline of 12%", "suffered $40,000 loss") is read as its
  size. The probe sentence keeps the wording, so the comparison is still of sizes.

**The first count is a text match.** "Contain 'within +/-' or the plus-minus sign" counts
criteria whose text holds those characters. A tolerance written another way ("(+/- $1M)"
without "within", or a range) is not counted and not read.

## Limits

- **The reader is careful, not proven. Read the review list.** It was audited three
  times by sessions that did not write it, each told to break it.
  - First version: of 103 hostile criteria, 23 were accepted and read wrongly, and 34
    more were accepted that have no safe reading.
  - After a first rewrite: of 414 new hostile criteria, 74 were read with a wrong
    value, tolerance or sign.
  - It was then rebuilt as an allow-list. Of 250 new hostile criteria aimed at its weak
    points, 147 were accepted and 55 of those were read wrongly, mostly by taking the
    wrong number for the value.
  - The lead-in-word rule above was then added. On those same 250 criteria the reader
    now accepts 86, and reads 81 as the auditor expected; the other 5 are a bit rate
    read as basis points (2), and three readings that are arguable. That figure is not
    an independent measure, because those criteria were used to make the fix. **The
    final reader has not had its own audit.**
  Hostile criteria are written to break the reader, so these rates say nothing about a
  normal rubric. They say the reader can be wrong, which is why the review list exists.
- **The wording it reads is narrow.** It was written for one benchmark's rubric (DRACO)
  and has not been tried on a second. On a rubric written differently, expect most
  criteria to be left out, with the reason.
- **Built sentences are not real responses.** A probe states one value in one short
  sentence, sometimes to more decimal places than a real response would, and sometimes
  ungrammatically ("Sales was $5M."). It tests the comparison, not how a grader finds a
  figure in a long text. Use `context` to test the second, by placing probes in real
  documents.
- **It does not run the grader, and does not prove the grader gave the verdicts in the
  file.** Keep your call records beside the receipt.
- **A probe at 1.1 tolerances is a hard case by design.** An error rate there is not an
  error rate on typical responses.
- **Receipts.** `verify` on a contracts file re-reads the rubric. `verify` on a probes
  receipt checks the contracts file and re-builds the probes from it; it does not look
  at the rubric. A contracts file that was edited by hand builds no probes.
- **Arithmetic** is exact decimal arithmetic on the digits as written, carried to 100
  digits. Numbers of more than 20 digits are not read.
