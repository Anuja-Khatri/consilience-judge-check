# Independent audit of the new `rubric` commands, and what was done about it

20 Nov 2026. The commands `consilience rubric scan`, `rubric probes`, `rubric table` and the per-item report in `grader-check` were written on the same day they were first used. Before anything was built on them they were given to a separate AI session that had not written them, with the code, the tests, the docs and the dataset, and told to break them. It made no model calls.

**The headline.** The study's numbers reproduced exactly. But the safety claim of the reader ("a criterion is read correctly or left out, never read wrongly") was false: of 103 hostile criteria the auditor wrote, 23 were accepted and read wrongly and 34 more were accepted when no safe reading exists. None of the 76 DRACO criteria was affected.

**What it is not.** Not a human review. The auditor is the same kind of system as the author.

## What was done about each finding

| # | Finding | What changed |
|---|---|---|
| 1 | The reader accepts some criteria and reads them wrongly: an unknown scale word after a tolerance ("$5 mil") was dropped; "5% relative" read as points; "8,849 m" read as millions; "41,5%" read as 415; a date mask ate part of a value ("2024.50", "June 12,500"); ".85" read as 85 | The reader was rewritten around one rule: every part of the number, unit and tolerance must be understood, otherwise the criterion is left out. A word after a money or percent tolerance is refused. Without a "$", single letters after a number are not scales. Commas must be regular thousands separators. A number that touches a masked date, another digit, a letter or a full stop is refused |
| 2 | 34 more accepted that should be left out: lost signs ("- $3.2M", "negative", em dash), other currencies read as dollars or as counts (C$, HK$, €, ¥), "$2.5 trillion" read as 2.5, one-sided or hedged wording (exceeded, almost, circa, "was not", "as high as"), numbers in words | Minus signs of every kind and the words "negative" and "minus" are refused. Other currency signs, a letter before "$", and currency words are refused. Magnitude words that are not read are refused. The list of wording that is not read was widened |
| 3 | The worked example in the docs did not match its own commands | The example was rewritten from a real run, with the full verdicts file shown |
| 4 | The rounding count treated "cannot be worked out" as "not outside", and "rounding" was really truncation toward the reference | The report now gives three numbers: accepted values still outside after ordinary rounding, still outside even when rounded toward the reference, and how many could not be checked |
| 5 | Item counting merged or dropped silently: empty item cells, an item in two clusters, tied largest clusters, items with only undecided rows; an empty table "agreed on every row" | Each is now counted and reported. An empty table says "nothing was checked" |
| 6 | Scan labels claimed more than they measured: "state a tolerance" was a text match; "wording needs judgement" also caught harmless "and"; the weight range left out the groups with none | Labels renamed and explained: "contain 'within +/-' or the plus-minus sign", `wording_not_read`, `number_like_tokens_N`, "in the N groups that have one" |
| 7 | `verify` on a probes receipt did not notice an edited contracts file or a missing probes file; damaged receipts gave a traceback | It now hashes the contracts file itself, requires the probes file, and reports a damaged receipt as an input error |
| 8 | Bad input gave Python tracebacks, not exit code 64 | Fixed for NaN and infinite weights and offsets, damaged contracts files, directories, missing output folders, empty offsets. Numbers of more than 20 digits are refused |
| 9 | Two tests compared the code with files the same code had written | Kept as regression tests, and joined by tests that do not: the auditor's hostile criteria (60 that must be left out, 11 that must be read right), a separate reader that re-reads the number out of every probe sentence, and tests for each damaged-file and edge case above |
| 10 | Sentences in the docs that claimed more than the code did | Rewritten. The docs now say the reader is "conservative, not proven" and tell the reader to check what it accepts on a new rubric |

**Unchanged by the rewrite:** the same 76 DRACO criteria are read, with the same values and tolerances, and the probes file is the same byte for byte (sha256 `147522f41376…`, the hash fixed in the Gemini preregistration). The contracts file was regenerated and its hash changed (from `6c8d25012b88…` to `5a57d645fd29…`) because its labels changed; the items in it did not.

**Two readings the auditor flagged that were kept, on purpose.** "40% (within +/- 5%)" is read as percentage points and is now flagged in the scan and in each such item (2 of DRACO's 76). "A decline of 12%" is read as the magnitude 12.

A second audit of the rewritten reader was then run. It broke it again (next section), and the reader was rebuilt a second time, as an allow-list. A third, narrower audit measured what is left. Both are below, after the first auditor's report.

## The first auditor's report, as returned

---

# Audit of `consilience rubric` / `grader-check` (by-item, cluster, rounding)

Verdict: the study's numbers reproduce exactly, but the central claim ("read correctly or left out, never read wrongly") is false, and one worked example in the docs does not match its own commands.

## Findings, most serious first

**1. CONFIRMED. `read_criterion` accepts criteria and reads them wrongly.** Of 103 adversarial criteria I wrote, 23 were accepted with a wrong value or tolerance. None of the study's 76 items is affected; this breaks the docs' safety claim and any other rubric.

| Criterion (accepted) | Read as | Probe labelled wrongly |
|---|---|---|
| `States revenue as $120 million (within +/- $5 mil)` (also `mln`, `bln`, `trillion`, `$2 hundred thousand`) | tolerance $5 | "$120.0000055 million" = unmet |
| `States gross margin as 40% (within +/- 5% relative)` | ±5 points | "42.5%" = met |
| `States summit height as 8,849 m (within +/- 5)` (also `373 K`, `0.5 M`, `512 B`, `45 m`) | 8,849,000,000 ± 5 | "8,849.0000055 m" = unmet |
| `States gross margin as 41,5% (within +/- 0,5 ppts)` | 415 ± 5 | "417.5%" = met |
| `States the index close as 2024.50 (within +/- 10)` | 50 ± 10 | "2024.61" = unmet; "far" is 2024.90 |
| `States beta as .85 (within +/- 0.05)` | 85 ± 0.05 | "Beta as .85.055." |
| `States shares issued in June 12,500 (within +/- 100)` | 500 ± 100 | value wrong, verdicts right by accident |

Causes:
- For money and percent, any word after the tolerance number is discarded.
- K/k/M/m/B after a bare number always mean thousand/million/billion.
- Commas are stripped without checking grouping.
- The date mask runs first and can eat part of the value.

**2. CONFIRMED. A further 34 were accepted when they should have been left out.**
- Sign lost (6): `- $3.2M`, `negative $3.2M`, `minus 3.2%`, em dash, non-breaking hyphen, `a decline of 12%`.
- Wrong unit label (5): `C$9.7M` and `HK$9.7M` become USD; `€30.8B (within +/- 0.5B)` and `¥` become "count".
- Scale dropped on both sides (4): `$2.5 trillion` is read as 2.5 USD.
- One-sided, hedged or negated wording (19): exceeded, above, below, almost, circa, close to, "was not", "as high as" (sentence becomes "Growth as high was 12.5%."), a second number in words, and `X% (within +/- Y%)` silently read as points.

**3. CONFIRMED. The step 4 output in `docs/rubric.md` is not what its commands produce.** With the three-row verdicts file shown, the real output is `grader right: 1, lenient: 2, strict: 0`, lines 4 and 5, and `+1.1: 1 of 2 items wrong (9% to 91%) … in 1 of 1 clusters`. The doc shows 9/2/1, lines 8 and 14, and `1 of 4 … (5% to 70%) … 1 of 2 clusters`, which comes from an unshown 12-row file. Steps 1 and 2 and the `grader-check.md` example match (abridged).

**4. CONFIRMED. The rounding count treats "cannot be said" as "not still outside".** Four lenient rows with step empty, `abc`, `0`, or cross-unit print `of 4 accepted, 0 still outside after rounding`. "Rounding" is also truncation: $66.9M against $64M ± $2M counts as inside. The study is unaffected (all steps present, all rows same-unit).

**5. CONFIRMED. By-item counting merges or drops silently.**
- Empty `item` cells are merged into one item (4 cases gave `items: 2`).
- An item in two clusters keeps the first.
- A tie for largest cluster goes to the alphabetically first label; swapping labels flips "largest 0 of 2" to "2 of 2".
- Items with only undecided rows vanish from the item count.
- A header-only table exits 0 with "the grader agrees … on every row".
- No crash, and the Wilson interval is correct. The study has no ties (cluster sizes 39, 13, 9, …).

**6. CONFIRMED. Scan labels and counts on the dataset claim more than they measure.** I read all 131 left-out criteria, not a sample of 40.
- `quantities_in_the_claim_2` (10): all are "9M 2025/2024", a period label read as a quantity.
- `wording_needs_judgement` (69): at least 9 need no judgement, e.g. "research and development expenses as $57.9M" (trips on "and"), "net cash from operating activities", "cost of sales (production)", and two `$(7,707)` negatives.
- "state a tolerance: 207" counts only `within +/-` or `±`. It misses at least 8 (`(+/- £0.01m)` ×5, `$32.5B +/- 2%` ×2, `(within $4.50-$5.50 range)`) and includes at least 4 that only mention ±.
- "within a group, from 2.5% to 59.2%" omits the 90 of 100 groups at 0%.

**7. CONFIRMED. `verify` gaps.**
- `verify probes_receipt.json` prints `ok contracts hash … matches` after `contracts.json` is edited (I changed `checkable` to 400 and a weight); it compares the stored hash field, not the file. `verify contracts.json` does catch it.
- A missing probes file passes silently.
- A changed rubric is not seen by the probes receipt.
- A malformed receipt gives a `KeyError` or `JSONDecodeError` traceback.
- The study's `contracts.json` records an absolute scratch path, so it needs `--data` elsewhere. It verifies against my rebuilt rubric (sha 18262c75…).
- Caught correctly: changed rubric, changed or re-stamped contracts results, changed probes file, edited receipts.

**8. CONFIRMED. Tracebacks (exit 1) instead of exit 64.**

| Command | Input |
|---|---|
| `rubric scan` | weight `NaN` or `Infinity` |
| `rubric probes` | `--offsets` `NaN`, `sNaN`, `Infinity`, `1e400`; contracts that are `[]`, lack `result`, have an item without fields, or are a directory |
| `rubric probes` | a number of 29 or more digits (28 digits: silently wrong offsets) |
| any | `--out` or `--receipt` into a missing directory |

`--offsets ""` silently uses the defaults. `rubric table` raises a spurious "given twice" when blank and explicit `call` values mix.

**9. CONFIRMED. Tests are weaker than they look.**
- `test_the_published_study_is_rebuilt_from_its_criteria` compares `rubric.py` with output of `pilot/draco_contracts.py`, whose regexes it copies verbatim.
- `test_the_published_study_comes_out_of_the_product_alone` pins files the same code wrote. Six `grader.py` mutations are caught only by it: Wilson returning [0,1], wrong `other_clusters`, wrong strict count, ordinary rounding, wrong rounding direction, smallest cluster as largest.
- Mutations that survive everything:
  - the judgement list cut to "approximately|or";
  - `verify_scan` not checking the receipt hash or the re-run;
  - `verify_probes` not comparing the re-run or the on-disk file;
  - the duplicate check removed;
  - weight share fixed at 1;
  - exit 64 dropped;
  - wrong cluster text.
- Untested: any accepted-but-wrong reading, ties, rounding below an off-grid reference, CLI errors beyond one missing file.

**10. Docs that claim more than the code does.**

| Sentence | Supportable version |
|---|---|
| rubric.md: "Other currencies, physical units, ranges and tolerances given as a percentage of the value are not read in this version." | They are not recognised; some are read wrongly (findings 1 and 2). |
| "contains exactly one quantity, and it is positive" | A sign is seen only as a hyphen or minus touching the number. |
| "Dates and period labels … are not taken for quantities." | "9M 2025" is; "2024.50" is taken for a date. |
| "The table carries nothing about the right verdict." (also the table's header comment) | `group` is the offset (+1.1, 0, far), which fixes the verdict; `grader-check` does not use it. |
| "`no_trailing_tolerance`: A plus-or-minus appears…" | Only `±` or `within +/-` is detected; `(+/- $0.5B)` is not counted at all. |
| "how often the graded version pays for a wrong answer" | How often the grader accepts built out-of-tolerance sentences (the Limits section says this). |
| grader-check.md: "How many accepted values are still outside…" | Rows where it cannot be computed count as not outside. |
| rubric.py: "All arithmetic is exact…" | Exact to 28 significant digits. |

## Checked and found sound

- **Scan of the dataset:** 3,934 criteria, 207, 23 of 100 groups, 76 checkable in 10 groups, weight 664 of 30,724 (2.16%), recomputed from `test.jsonl`. All 76 values, tolerances and units are right by eye and by my own parser.
- **Dataset probes at the 15 offsets:** 1,083 probes, 57 skipped. Each sentence holds exactly one number; stated value, offset and verdict all match; the 152 edge probes are all met; `far` is at least 4 tolerances away. Fourteen of 76 sentences are ungrammatical ("sales was"), meaning unchanged. My 24-criterion awkward rubric gave 318 probes with no mismatch.
- **Study table:** rebuilt from the two `judge_calls.jsonl` files and the item files, with no package code. 3,051 rows, no differences; 2872 right, 139 lenient, 40 strict. Text hashes matched for 2,568 rows; the 483 in-report rows cannot be hash-checked from the repo. No saved verdict differs from the judge's reply.
- **By-item numbers:** all 15 groups are identical to `grader_check_saved.txt`.

| Group | Wrong / items | Every row | Clusters | Largest | Still outside |
|---|---|---|---|---|---|
| +1.1 | 10 / 76 | 8 | 6 / 10 | 1 / 39 | 5 |
| -1.1 | 22 / 76 | 20 | 6 / 10 | 15 / 39 | 17 |
| +1.1:report | 14 / 69 | 14 | 8 / 9 | 6 / 39 | 11 |
| +1.5 | 3 / 76 | 1 | 3 / 10 | 0 / 39 | 2 |
| 0 | 0 / 76 | 0 | 0 / 10 | 0 / 39 | n/a |
| far | 0 / 76 | 0 | 0 / 10 | 0 / 39 | n/a |

- **Old receipts:** only two files are named `grader_receipt.json` (draco_contracts, draco_replication). Both verify and re-run to identical content. `wrong_law_receipt.json` and the three product receipts also verify.
- **`rubric table`:** ids with `:`, `#`, `@`, commas, quotes and tabs, and criteria with newlines, round-trip. Unknown ids and duplicates exit 64; unknown verdict words become `grader_verdict_unreadable` (exit 3).
- 48 of 48 tests pass.

---

# The second audit, and what was done about it

**The headline.** 414 new hostile criteria. The rewritten reader accepted 231 and read 74 of them with a wrong value, tolerance or sign. The study was untouched: its 76 criteria, its probes and its receipts all reproduced.

**The lesson.** The first rewrite added rules to a block-list: "refuse this, refuse that". A block-list over free text cannot be completed, and the second audit showed it. The reader was rebuilt as an allow-list.

| # | Finding | What changed |
|---|---|---|
| 1 | The date mask hid part of a value: "the S&P 500 closing level as 2059" read as 500; "1.2024" read as 1; "2.5-year" read as 2 | No masking any more. The claim is cut into words, and every word that holds a digit must be recognised in full as a date label or as the one value. "1.2024" is now read as 1.2024. A bare year or a duration label beside a bare whole number is refused as unclear |
| 2 | A tolerance without the value's scale was read literally: "8.1 billion (within +/- 0.1)" as ± 0.1; "$30.8B (within +/- $0.5)" as 50 cents | If the value has a scale the tolerance must have one too |
| 3 | Decimal commas and fraction characters: "0,385" read as 385; "$3½" read as 3 | A number may not start with a zero group before a comma. Only plain ASCII text is read |
| 4 | 28 lost signs: other kinds of hyphen and minus, thin spaces and tabs after a minus, "neg", "-ve", a trailing minus | Non-ASCII text and control characters are refused outright. "neg", "-ve", a minus or bracket on the number word, and a lone "-" before it are refused |
| 5 | Tolerance units misread: "5,772 kelvin (within +/- 5K)" as 5,000; "500 MW (within +/- 10 mW)" matched without regard to case | On a count only a small "k" written against the number is a scale, and not when the value carries a short unit ("kg"). Unit words are compared letter for letter |
| lower risk | Magnitude words that are not read ("trn", "Mrd", "$5-million"), other currencies by code or country, "$10%", hedges such as "in excess of", "topped", "thirteen" | Lists widened; hyphenated and odd-shaped value words are refused by the word rule |
| 6 | `grader-check`: empty cluster cells merged; one item label on rows with different references; repeated ids; a probes file with one probe twice; two cases shown only in the JSON | Each is counted and printed. A probe twice in a probes file is refused |
| 7 | `verify` accepted a probes receipt whose counts were edited and re-hashed; it looked in the working folder before the receipt's folder; several inputs gave tracebacks; one input hung | The whole recomputed result is compared. The file beside the receipt is used first. A contracts item must be exactly what the reader makes of its criterion, so an edited file builds no probes. Numbers with exponents and oversized weights are refused. Criteria over 600 characters are refused, which removes the hang |
| 8 | Docs: the worked example matched, but the Python example failed on its own, and several sentences claimed more than the code did | Rewritten. The docs no longer say the reader never misreads. They say it is careful, not proven, and tell the user to read a review list of everything it accepted (`rubric scan --review`) |

**Measured on the second auditor's own corpus after the rebuild** (not out-of-sample, since it was used for the fix): 70 of 414 accepted; 1 was read wrongly before a last rule was added ("10-year for 3 stores"), 0 after; 3 have an imprecise unit label with the numbers right.

**Still unchanged:** the same 76 DRACO criteria, read the same way; the probes file byte for byte (sha256 `147522f41376…`). The contracts file was regenerated again because its labels changed (final hash, after the third audit: `f446bc0051c7…`).

## The second auditor's report, as returned

---

# Audit 3 of `consilience.rubric`: the safety claim does not hold

I wrote 414 new hostile criteria (none overlap the test lists). The reader accepted 231 and read 74 of them with a wrong value, tolerance or sign. None of this touches the study: its 76 items, probes and three receipts all reproduce.

## Findings, most serious first

All are CONFIRMED by running the code. Findings 1–5 break the safety claim, 6–7 are robustness, 8 is docs.

**1. The date mask hides part of the value.** A bare 19xx/20xx run or an `N-year/-month/-day/-week` label is masked even when it belongs to the value, and the "touches a date" test misses it.

| Criterion | Read as | Probe at +1.1 |
|---|---|---|
| `States the S&P 500 closing level as 2059 (within +/- 10)` | 500 ± 10 | "The S&P 511 closing level as 2059." |
| `States the exchange rate as 1.2024 (within +/- 0.005)` | 1 ± 0.005 | "The exchange rate was 1.0055.2024." |
| `States a 2.5-year payback (within +/- 0.5)` | 2 ± 0.5 | "A 2.55.5-year payback." |

`$1.2025` → $1, `12.2000` → 12 and `1.1987` → 1 go the same way; 15 such cases in all.

**2. A tolerance without the value's scale word is read literally.**
- `States world population as 8.1 billion (within +/- 0.1)` → 8,100,000,000 ± 0.1. The +1.1 probe is "World population was 8.10000000011 billion.", marked unmet.
- `States revenue as $30.8B (within +/- $0.5)` → ± $0.50.
- Seven cases; the same input without the `$` on the tolerance is already refused as `tolerance_kind_unclear`.

**3. Decimal comma and vulgar fractions.**
- `States the Gini coefficient as 0,385 (within +/- 0,005)` → 385 ± 5; probe "The Gini coefficient was 390.5."
- `States the coupon as $3½ (within +/- $0.25)` → $3; probe "The coupon was $3.275½."
- Eight cases.

**4. Sign lost (28 cases).** The probe sentence keeps the mark, so verdict arithmetic is unaffected, but the item is stored positive.
- Minus-like characters not in the list: U+2010, U+FF0D, U+FE63, U+207B, U+208B, U+2796, U+02D7, U+2015, U+FE58, U+2E3A.
- Anything other than a space or NBSP between a minus and the number: thin space, narrow NBSP, tab, newline, zero-width space.
- Wording and position: `neg`, `neg.`, `-ve`, `negative:`, `a negative of`, and a trailing minus (`$3.2M-`).

**5. Tolerance unit misread.**
- `5,772 kelvin (within +/- 5K)` → ± 5000.
- `500 MW (within +/- 10 mW)` and `500 MB (within +/- 10 Mb)` → ± 10, because the unit word is compared without case.

**Lower-risk misreads.**
- Unlisted or hyphenated scale words after `$` are read as bare dollars: `$2.5 trn`, `$5 Mrd`, `$5 bil`, `$5-million`, `$30.8 Mill.`. Twelve cases, reachable only with a bare-dollar tolerance.
- Unit label wrong but arithmetic consistent (21): `9,600 bps` bitrate read as 96 percent, `₱30,800` and `30,800 €` read as counts, `$5M NZD` and `Canadian $5M` read as USD, `$10%` read as a percentage.
- Wording the docs say is not read, accepted with numbers as written (24): `in excess of`, `topped`, `never`, `cannot`, `ca.`, `∼`, `$30B+`, `thirteen`.

**6. grader-check: new cases that are silently merged or only half reported.**
- Empty `cluster` cells merge into one nameless cluster, which can become the "largest".
- One item label on rows with different reference, unit and tolerance counts as one item.
- Identical rows with the same id are each counted.
- `rubric table`: a probes file with a `probe_id` twice lets the later row win silently.
- Two cases are reported in JSON only, not in the printed report: an item in two clusters, and a table where every item cell is empty.

**7. Receipts and command line.**
- `verify` says ok on a probes receipt whose `result.probes`, `items`, `skipped` or `output.bytes` were edited and the hash recomputed; the re-run compares only the CSV hash.
- `verify` looks in the working directory before the receipt's folder, so a changed `probes.csv` beside the receipt passes if a clean copy sits at the recorded relative path.
- Tracebacks:
  - `grader-check t.csv --receipt no/such/r.json` (also a directory).
  - `grader-check` on the row `a,1e40,USD,10 USD,1e41,USD,met,g,A,t,1` → `decimal.InvalidOperation`.
  - `rubric scan` with weight `1e999999999` → `decimal.Overflow`.
  - `rubric probes` on a contracts file that passes the field check but holds wrong types (`span: "ab"`, `written.scale: "0"`, `value: "NaN"`, missing `written.unit_text`): 17 of 22 variants.
  - `verify` on a probes receipt over such a file.
- Hang: `rubric scan` on a tolerance of `1` + 120,000 spaces + `!` runs past 120 s.

**8. Docs.** The worked example in `docs/rubric.md` matches line for line. Two gaps: the scan block drops its last two lines unmarked, and the Python block fails on its own (`file not found: probes.csv`) because it never writes that file. Sentences that claim more than the code does:
- "a criterion is read only if every part of its number, unit and tolerance is understood"
- "A minus sign of any kind, or the words "negative" or "minus", before the number"
- "Another currency sign, … or a currency named in words"
- "a magnitude or unit that is not understood"
- "If the tolerance carries a word too, it must be the same word"
- "One reading is a choice, and it is flagged." Reading (b), a decline or loss read as its magnitude, appears nowhere in `docs/rubric.md`, the module docstring or the changelog, yet the study uses it once ("Hayes suffered $40,000 loss"). `12 percent (within +/- 1 percent)` is choice (a) but is read as a count and not flagged.
- "exact decimal arithmetic on the digits as written" (also in `grader-check.md`) holds to 28 significant digits. `States the count as 12345678901234567890 (within +/- 0.000000001)` gives +1.1, +2 and −1.1 probes that all state the reference and are marked met.

## Checked and found sound

**Check 1 counts.**

| | n |
|---|---|
| Written | 414 |
| Left out | 183 (76 a careful person could read) |
| Accepted | 231 |
| – read right | 98 |
| – wrong value | 35 |
| – wrong tolerance | 11 |
| – sign lost | 28 |
| – unit label only | 21 |
| – unlisted wording | 24 |
| – arguable notation | 14 |

**Check 2.**
- Dataset: 1,007 probes at the 14 offsets, re-read with my own parser. There were 0 value mismatches and 0 verdict mismatches, both edges are met, and nothing but the number (and the unit for `u` probes) changes.
- 915 dataset sentences hold a second number; it is always a date or period label copied from the criterion.
- Hostile accepted: 2,915 probes, with real problems in 35 items, all in the wrong-value, wrong-tolerance or sign classes above.

**Check 3.**
- Scan: 3,934 criteria, 207 with a tolerance, 76 items; the `result` equals the study's.
- Probes: 856, byte-identical, sha256 `147522f41376131e…`.
- Receipts: all three verify ok. `contracts.json` records an absolute scratch path, so it verifies without `--data` only on this machine.
- The study table has no empty item or cluster cells, no item with two references, no duplicate ids and no cross-unit rows.

**Check 4.** Of the 106 "States" criteria left out:

| Reason a careful person could still read it | n | Example |
|---|---|---|
| "9M 2025" counted as a number | 10 | `States 9M 2024 total interest expense as $49,434 thousand (within +/- $200k)` |
| Harmless and/or/from/slash/brackets | 9 | `States 180 reams consumed or used (within +/- 10 reams)` |
| One value written twice | 26 | `…as $1,116.6m or $1.12bn (within +/- $5m)` |
| Hedge beside an explicit tolerance | 10 | `…raised approximately $51 million (within +/- $3M)` |
| A rate | 2 | `$17/user/month (within +/- $1)` |
| Value with supporting figures | 3 | `+3.9% from $2,612.2M to $2,714.7M (within +/- 0.3pp)` |
| Negative (by design) | 7 | `$(7,707) thousand…` |
| Canadian dollars (by design) | 11 | `C$9.7M or C$9,745,686…` |
| Not one value | 28 | — |

`--lead Calculates` adds 2 more.

**Check 5.** These are reported correctly: some empty item cells, tied largest clusters, items with only undecided rows, a header-only table ("nothing was checked", exit 0), a step that is empty, 0, non-numeric, negative, NaN or Infinity ("6 could not be checked"), and cross-unit rows (decided by float, edge left undecided, rounding not checked).

**Check 6.** `verify` was not fooled by an edited contracts file (with or without a recomputed hash), an edited rubric, `probes.csv` or table, or an edited grader summary or options.

One slip: I wrote a scratch file `hostile.json` into the repo root by mistake and deleted it. Nothing in the three read-only folders has changed since.

---

# The third audit, and what was done about it

**The headline.** 250 new hostile criteria, aimed at the allow-list's weak points after reading its source. 147 were accepted and **55 of those were read wrongly**: 17 with the wrong value, 7 with value and tolerance both off by one factor, 1 lost sign, 30 accepted where no safe reading exists. The probe builder itself was sound: in all 1,235 sentences the number, the verdict and the wording were consistent with what the reader had read.

**The main cause.** The reader still guessed which number was the value. "The Top 1,000 customers' average order as 1999" was read as 1,000, because 1999 looks like a year.

| Cause | What changed |
|---|---|
| The wrong number taken for the value (a label number, or a value hidden as a year or a day of the month) | The value must now come straight after one of a few lead-in words: "as", "was", "is", "of", "issued", "provided", "suffered" (the words that precede the value in DRACO's 76 criteria, plus "was" and "is"). A number anywhere else is not guessed at: the criterion is left out. A year-like number right after a lead-in word is refused as unclear. Short month names count as months |
| A scale word with punctuation or a hyphen after the value ("million,", "thousand,", "billion-plus", "lacs") | The word after the value is refused if it begins with a scale word |
| A scale stated elsewhere ("in millions", "in $bn") | Refused |
| More one-sided and hedged wording (upto, at-least, larger than, short of, nearing, plus, odd, est., abt, ca), clock times, versions | Added to the wording that is not read |
| "bps" as a bit rate read as basis points | Not fixed. The numbers stay consistent, the unit label is wrong |

**Measured after the change, on the third auditor's own 250 criteria** (not an independent measure, because they were used for the fix): 86 accepted, 81 read as the auditor expected. The other 5: a bit rate read as basis points (2), and three arguable readings ("kelvin (within +/- 5k)", "1.234 staff", a date written as digits). On the second auditor's 414: 65 accepted, 3 not as expected (two unit labels and a decimal point that may be a thousands separator).

**What this adds up to.**

- Three audits, three rounds of fixes, and each audit of a "fixed" reader found new misreads. **The final reader has not had an audit of its own.** Another one would very likely find more.
- So the claim is not, and must never be, that the reader cannot misread. The claim is: it reads a narrow pattern, leaves the rest out, and writes a list of what it accepted for a person to check (`rubric scan --review`).
- For DRACO that check has been done three times over: the 76 accepted criteria were read by me and by two of the auditors, value by value, and are right.
- The rates above are for criteria written to break the reader. They say nothing about how it does on a real rubric, and it has met only one.

**Unchanged by every rewrite:** the same 76 DRACO criteria, read the same way, and the probes file byte for byte (sha256 `147522f41376…`).

## The third auditor's report, as returned

---

# Audit 4 of `read_criterion`: the rebuilt reader still misreads

**Of 147 accepted, 55 were read wrongly**: 17 wrong value, 7 value and tolerance both off by one factor, 1 sign lost, 30 accepted with no safe reading. Six more are label-only. No tolerance was wrong on its own.

This is a hostile sample, not an estimate for a real rubric. I read the source first and aimed at its weak points. Expectations were frozen (sha256 `84283c04…`) before the reader ran. No case repeats an earlier corpus.

- **Plausible wording:** 38 of 125 accepted were read wrongly.
- **Contrived wording:** 17 of 22.
- **Verdict arithmetic:** wrong in 30 of the 55, right only on an assumption in 10, unaffected in 11, unclear in 4.

## Check 1 counts

| | n |
|---|---|
| Written | 250 |
| Left out | 103 |
| Accepted | 147 |
| Read right | 86 |
| Label-only | 6 |
| Wrong value | 17 |
| Wrong tolerance | 0 |
| Value and tolerance off by the same factor | 7 |
| Sign lost | 1 |
| Accepted, no safe reading | 30 |

- **Left out (103):** 10 are sanity cases refused by design, 26 had no safe reading, and 67 are lost coverage where a careful person reads a value (for example "year-over-year" trips `over\b`).
- **Read right (86):** includes 1 flagged percent-as-points, 3 stated declines and 3 losses by idiom (deficit, unfavorable, short), none counted as misreads.

## Root causes

| Cause | Where in `rubric.py` | Cases |
|---|---|---|
| A label number with a comma or decimal escapes the year check while the real value (bare 19xx/20xx, "10-year") is masked | line 271 | 8 |
| A 1–2 digit value after a month name is masked as a day; another bare label number becomes the value | line 229 | 6 |
| Scale word with punctuation or a hyphen ("million,", "thousand,", "bn,", "billion-plus", "lacs") is dropped | lines 253, 269 | 12 |
| Scale stated elsewhere ("in millions", "in $bn") is dropped | — | 5 |
| "bps" as bit rate read as basis points | — | 2 |
| Deny-list gaps: upto, at-least, larger than, just short of, nearing, plus, odd, est., abt, ca | line 114 | 10 |
| Label digit taken when the value is in words or absent | — | 5 |
| Clock times, a version, a date as digits | — | 4 |
| "subzero" | — | 1 |
| Arguable | — | 2 |

With a properly scaled tolerance, the punctuated-scale criteria are refused instead, as `tolerance_not_smaller_than_value`.

## Wrong value (17)

All criteria begin "States".

| Criterion | Read | Expected |
|---|---|---|
| the Top 1,000 customers' average order as 1999 (within +/- 5) | 1000 | 1999 |
| the 12.5 mile route's total elevation gain as 2050 (within +/- 10) | 12.5 | 2050 |
| the 2.5x leveraged fund's closing level as 2050 (within +/- 1) | 2.5 | 2050 |
| the 3.5 inch drive shipments as 2040 (within +/- 1) | 3.5 | 2040 |
| the 1,000 Genomes sample count as 2054 (within +/- 10) | 1000 | 2054 |
| the lease term as 10-year for 3,500 square feet (within +/- 1) | 3500 | 10 |
| the Windows 8.1 active installs as 1975 (within +/- 5) | 8.1 | 1975 |
| the 0.75 inch pipe fittings ordered as 2016 (within +/- 0.5) | 0.75 | 2016 |
| Fortune 500 respondents as a thousand (within +/- 50) | 500 | 1000 |
| Form 10 filings received in May 25 (within +/- 2) | 10 | 25 |
| Boeing 737 deliveries in June 45 (within +/- 5) | 737 | 45 |
| Phase 3 trial sites opened in March 12 (within +/- 2) | 3 | 12 |
| Section 8 vouchers issued in April 60 (within +/- 5) | 8 | 60 |
| Week 12 units shipped in June 30 (within +/- 2) | 12 | 30 |
| the Top 40 entries charting in July 12 (within +/- 2) | 40 | 12 |
| total debt as $9,500,000 thousand, net (within +/- $50k) | 9,500,000 | 9,500,000,000 |
| shares outstanding as 153,000 thousand, diluted (within +/- 2k) | 153,000 | 153,000,000 |

## Same factor (7)

Verdicts are unaffected for same-scale sentences, but the value is not in base units.

| Criterion | Read | Expected |
|---|---|---|
| the modem speed as 56,000 bps (within +/- 500 bps) | 560 ± 5 percent | 56,000 ± 500 |
| the serial link rate as 9600bps (within +/- 100bps) | 96 ± 1 percent | 9,600 ± 100 |
| revenue in millions as $1,234 (within +/- $10) | 1234 ± 10 | 1.234e9 ± 1e7 |
| net income in thousands as $16,183 (within +/- $200) | 16183 ± 200 | 16,183,000 ± 200,000 |
| shares outstanding in thousands as 705,593 (within +/- 500) | 705593 ± 500 | 705,593,000 ± 500,000 |
| total assets, in billions, as $12.4 (within +/- $0.2) | 12.4 ± 0.2 | 1.24e10 ± 2e8 |
| capex in $bn as 3.2 (within +/- 0.1) | 3.2 ± 0.1 count | 3.2e9 ± 1e8 USD |

## Sign lost (1)

"the low as 5 degrees subzero (within +/- 1)" was read as 5 (contrived).

## Accepted with no safe reading (30)

| Criterion | Read | Why unsafe; verdict arithmetic |
|---|---|---|
| revenue as $120 million, up sharply (± $5) | 120 ± 5 | tolerance unscaled; right only if meant in the same scale |
| net sales of $4.2 billion, a record (± $0.1) | 4.2 ± 0.1 | same |
| subscribers as 260 million, a record (± 5) | 260 ± 5 | same |
| a $1.2 billion-a-year run rate (± $0.1) | 1.2 ± 0.1 | same |
| assets of $5 bn, mostly loans (± $1) | 5 ± 1 | same |
| revenue as $120 million: a record (± $5) | 120 ± 5 | same |
| revenue as $5 mm, net of returns (± $1) | 5 ± 1 | same |
| the population as 8.1 billion, rounded (± 0.1) | 8.1 ± 0.1 | same |
| the loan sanctioned as 45 lacs (± 2) | 45 ± 2 | same |
| the backlog as $30 billion-plus (± $1) | 30 ± 1 | one-sided and unscaled; wrong |
| the headcount as 500 plus (± 20) | 500 | one-sided; wrong |
| a discount of upto 15% (± 1 ppts) | 15 | one-sided; wrong |
| revenue of at-least $5M (± $0.5M) | 5M | one-sided; wrong |
| revenue larger than $5M (± $0.5M) | 5M | one-sided; wrong |
| revenue just short of $5M (± $0.5M) | 5M | one-sided; wrong |
| revenue nearing $5M (± $0.5M) | 5M | hedged; wrong |
| the stock of homes as 30 odd (± 2) | 30 | hedged; right for the literal number |
| revenue as est. $30.8B (± $0.5B) | 30.8B | hedged; right for the literal number |
| revenue as abt $30.8B (± $0.5B) | 30.8B | hedged; right for the literal number |
| revenue as ca $30.8B (± $0.5B) | 30.8B | hedged; right for the literal number |
| the Big 4 audit fee total as a million (± 0.5) | 4 | value in words; wrong |
| zero defects across 400 inspected units (± 5) | 400 | two quantities; unclear |
| the Sept 30 headcount (± 2) | 30 | no value stated |
| the Dec 31 share count in thousands (± 5) | 31 | no value stated |
| the meeting start as 10.30 am (± 0.15) | 10.3 | clock time; wrong |
| the departure as 1430 hours (± 30) | 1430 | clock time; wrong |
| the Python release as 3.11 (± 0.01) | 3.11 | version label; wrong |
| the filing date as 20240930 (± 1) | 20240930 | a date; wrong |
| the core temperature as 15,000,000 kelvin (± 5k) | ± 5000 | arguable: 5k or 5 K |
| headcount as 1.234 staff (± 0.050) | 1.234 | arguable: European 1,234 |

## Label-only (6)

- "report length as 48pp (± 2pp)" was read as percent.
- "spread as 425 basis points (± 10)" and "spread in bps as 425 (± 10)" were read as count.
- "R&D as a percentage of sales as 12.5 (± 0.5)" was read as count.
- "$120M ARS" and "$5M TWD" were read as USD.

## Check 2: probe sentences

I built 1,235 sentences for 149 items. That is the 147 plus two sanity cases that `scan_rubric` accepts after trimming spaces; both read right. 105 `+1.1u` probes and one `-1.1` probe were skipped by the builder.

The builder itself is sound. In all 1,235 sentences:
- the re-read number equals `stated_value`;
- `right_verdict` matches exact decimal arithmetic;
- the old number is replaced;
- sign, currency and unit are unchanged in non-`u` probes;
- the other words are untouched.

The faults are inherited from Check 1 or are minor:

- **Scale ignored:** in 147 sentences across 18 misread items, the sentence carries a scale that `stated_value` ignores, such as "Revenue was $125.5 million, up sharply." with `stated_value` 125.5. All eight offsets of each of the 18 items are affected, plus the three `+1.1u` sentences below.
- **Garbled `+1.1u` sentences (3):**
  - "Total debt was $9.555 million thousand, net."
  - "Revenue in millions was $1.245 thousand."
  - "Net income in thousands was $16.403 thousand."
- **Verdict opposite to the sentence:** for the 17 wrong-value items, 53 of 136 sentences carry a `right_verdict` opposite to what the sentence states.
  - 45 are "unmet" while the real value is untouched, such as "The Top 1,005.5 customers' average order as 1999."
  - 8 are "met" for the two "thousand," items.
- **`+1.1u` drops a written "+":** "The gain was +$1.5M." became "The gain was $1,610 thousand."
- **Grammar only (2):** "Revenue was reported was $5.2M." and "The board is described was 9 members strong."
- **Cosmetic (1):** "IPhone".

## Not tried

- Non-ASCII beyond 5 cases and other lead words beyond 4.
- Criteria over 600 characters, CSV quoting, weights and `--where`.
- The M-as-thousand convention.
- Non-English number words.
- Random or fuzzed generation.
- Any real rubric.
- Any grader's behaviour on the probes.
