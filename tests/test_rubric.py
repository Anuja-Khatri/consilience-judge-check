"""`scan`, `probes`, `table`: find the criteria of a rubric that arithmetic can check, build
probes whose right verdict is fixed by arithmetic, and join a grader's verdicts into the
table `check` reads. No grader and no model is run anywhere. All data here is made up,
except the last test, which re-reads the criteria of a published study."""

from __future__ import annotations

import csv
import io
import json
from decimal import Decimal
from pathlib import Path

import pytest

from consilience_judge_check import build_probes, check_grader, probe_table, scan_rubric, verify
from consilience_judge_check.cli import main
from consilience.compare import InputError
from consilience_judge_check.rubric import CONTRACTS_SCHEMA, read_criterion

RUBRIC = """id,group,section,weight,criterion
c1,taskA,facts,10,States Q3 revenue as $30.8B (within +/- $0.5B)
c2,taskA,facts,5,"States headcount as 12,400 employees (within +/- 200)"
c3,taskA,facts,5,States gross margin as 41.5% (within +/- 0.5 ppts)
c4,taskA,facts,8,States revenue grew approximately 12% (within +/- 1%)
c5,taskA,style,4,Uses clear section headings
c6,taskB,facts,6,States the exam fee as $93 (within +/- $10)
c7,taskB,facts,-5,States net debt as $64M (within +/- $2M)
c8,taskB,facts,3,Reports net debt as $64M (within +/- $2M)
c9,taskB,style,2,States capex as $120M (within +/- $5M)
c10,taskC,facts,7,States the sample mass as 5 kg (within +/- 100 g)
"""


def _write(tmp_path, text, name="rubric.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_a_criterion_with_one_value_and_a_tolerance_is_read_exactly():
    item, why = read_criterion("States Q3 revenue as $30.8B (within +/- $0.5B)")
    assert why is None
    assert (item["kind"], item["unit"], item["value"], item["tolerance"]) == \
        ("money", "USD", "30800000000", "500000000")
    assert item["step"] == "100000000"          # one unit of the last digit written: $0.1B
    assert item["claim"][slice(*item["span"])] == "$30.8B"


@pytest.mark.parametrize("text,reason", [
    ("Reports revenue as $30.8B (within +/- $0.5B)", "does_not_start_with_a_lead_word"),
    ("States revenue as $30.8B", "no_trailing_tolerance"),
    ("States revenue as approximately $30.8B (within +/- $0.5B)", "wording_not_read"),
    ("States revenue as $30.8B or more (within +/- $0.5B)", "wording_not_read"),
    ("States revenue rose to $30.8B with margin 41% (within +/- $0.5B)", "number_not_read"),
    ("States revenue as $30.8B with margin as 41% (within +/- $0.5B)", "number_like_tokens_2"),
    ("States cash flow as -$3.2M (within +/- $0.5M)", "negative_value"),
    ("States revenue as $30.8B (within +/- 0.5 billion)", "tolerance_kind_unclear"),
    ("States revenue as $30.8B (within +/- 0.5B)", "tolerance_not_read"),
    ("States margin as 41.5% (within +/- $1M)", "tolerance_kind_differs"),
    ("States revenue as $3M (within +/- $5M)", "tolerance_not_smaller_than_value"),
    ("States power as 5000 W (within +/- 0.5 kW)", "tolerance_unit_differs"),
    ("States revenue as \u20ac30.8B (within +/- \u20ac0.5B)", "characters_not_read"),
    ("States revenue as $30.8B (within \u00b1 $0.5B)", "characters_not_read"),
])
def test_everything_else_is_left_out_with_a_reason(text, reason):
    item, why = read_criterion(text)
    assert item is None and why == reason


# Found by an independent audit of the first version of the reader, which accepted these
# and read them wrongly, or accepted them when no safe reading exists. Each must be left out.
HOSTILE = [
    # a scale word that is not understood, on either side
    "States revenue as $120 million (within +/- $5 mil)",
    "States revenue as $120 million (within +/- $5 mln)",
    "States revenue as $30.8B (within +/- $0.5 bln)",
    "States market cap as $2.5 trillion (within +/- $0.1 trillion)",
    "States debt as $36.2T (within +/- $0.5T)",
    "States revenue as $5 Million (within +/- $1)",
    "States revenue as $64M (within +/- $2 hundred thousand)",
    "States revenue as $30.8B (within +/- $0.5B each)",
    # a relative tolerance
    "States gross margin as 40% (within +/- 5% relative)",
    "States revenue as $200M (within +/- 5%)",
    "States headcount as 12,400 (within +/- 5%)",
    # a letter after a bare number may be a unit, not a scale
    "States summit height as 8,849 m (within +/- 5)",
    "States depth as 10,935 m (within +/- 25 m)",
    "States boiling point as 373 K (within +/- 2)",
    "States concentration as 0.5 M (within +/- 0.05)",
    "States file size as 512 B (within +/- 16)",
    "States distance as 384,400,000 metres (within +/- 5 m)",
    "States capacity as 500MW (within +/- 10MW)",
    "States Avogadro constant as 6.022e23 (within +/- 0.01e23)",
    # separators
    "States gross margin as 41,5% (within +/- 0,5 ppts)",
    "States revenue as $1,5 million (within +/- $0,1 million)",
    "States beta as .85 (within +/- 0.05)",
    "States population as 1 234 567 (within +/- 10,000)",
    "States population as 1.234.567 (within +/- 10.000)",
    "States revenue as $30,800, a record (within +/- $500)",
    "States headcount as 12,40 (within +/- 2)",
    "States revenue as $1,00,000 (within +/- $5,000)",
    # a date or period label next to, or taken for, the value
    "States headcount as 2024 (within +/- 50)",
    "States Q5 revenue as $5.2B (within +/- $0.1B)",
    # the sign
    "States cash flow as - $3.2M (within +/- $0.5M)",
    "States net income as negative $3.2M (within +/- $0.5M)",
    "States the change as \u20143.2% (within +/- 0.5 ppts)",
    "States the change as minus 3.2% (within +/- 0.5 ppts)",
    "States the change as \u20113.2% (within +/- 0.5 ppts)",
    "States EPS as $-0.45 (within +/- $0.05)",
    # one-sided, hedged or negated
    "States revenue exceeded $30.8B (within +/- $0.5B)",
    "States revenue of almost $30.8B (within +/- $0.5B)",
    "States revenue above $30.8B (within +/- $0.5B)",
    "States revenue as circa $30.8B (within +/- $0.5B)",
    "States revenue as close to $30.8B (within +/- $0.5B)",
    "States revenue was not $30.8B (within +/- $0.5B)",
    "States growth as high as 12% (within +/- 1 ppts)",
    "States as many as 12,400 employees (within +/- 200)",
    "States revenue as $30.8B to the nearest billion (within +/- $0.5B)",
    "States revenue as $30.8B, up twelve percent (within +/- $0.5B)",
    "States the price as $17 a user a month (within +/- $1)",
    # other currencies
    "States revenue as \u20ac30.8B (within +/- 0.5B)",
    "States revenue as \u20ac30,800 (within +/- 500)",
    "States equity as C$9.7M (within +/- $0.1M)",
    "States revenue as HK$9.7M (within +/- $0.1M)",
    "States revenue as \u00a530.8B (within +/- 0.5B)",
    "States revenue as 30.8 billion yen (within +/- 0.5 billion)",
    # the tolerance is in another unit, or names another thing
    "States headcount as 12,400 employees (within +/- 200 staff)",
    "States 5,000 W power (within +/- 0.5 kW)",
    "States spread as 425 bps (within +/- 10)",
    # too long to keep exact
    "States the count as 123456789012345678901234567890 (within +/- 5)",
    # found by a second audit, after the first rewrite
    "States the S&P 500 closing level as 2059 (within +/- 10)",        # which is the value?
    "States the lease term as 10-year for 3 stores (within +/- 1)",
    "States a 2.5-year payback (within +/- 0.5)",
    "States world population as 8.1 billion (within +/- 0.1)",         # 0.1 of what?
    "States revenue as $30.8B (within +/- $0.5)",
    "States the Gini coefficient as 0,385 (within +/- 0,005)",
    "States the coupon as $3\u00bd (within +/- $0.25)",
    "States the change as \u20103.2% (within +/- 0.5 ppts)",           # another kind of hyphen
    "States the change as \u2212\u20093.2% (within +/- 0.5 ppts)",     # minus, thin space
    "States the change as -\t3.2% (within +/- 0.5 ppts)",
    "States net income as neg $3.2M (within +/- $0.5M)",
    "States the change as -ve 3.2% (within +/- 0.5 ppts)",
    "States cash flow as $3.2M- (within +/- $0.5M)",
    "States the temperature as 5,772 kelvin (within +/- 5K)",
    "States capacity as 500 MW (within +/- 10 mW)",
    "States the mass as 5,000 kg (within +/- 2k)",
    "States market cap as $2.5 trn (within +/- $0.1)",
    "States revenue as $5-million (within +/- $1)",
    "States revenue as $30.8 Mill. (within +/- $0.5)",
    "States the bonus as $50 grand (within +/- $5)",
    "States a $5 M&A advisory fee (within +/- $1)",
    "States the rate as $10% (within +/- $1%)",
    "States revenue as \u20b130,800 (within +/- 500)",
    "States revenue as $5M NZD (within +/- $0.2M)",
    "States revenue as Canadian $5M (within +/- $0.2M)",
    "States revenue as A $5M (within +/- $0.2M)",
    "States revenue in excess of $30.8B (within +/- $0.5B)",
    "States revenue topped $30.8B (within +/- $0.5B)",
    "States revenue surpassed $30.8B (within +/- $0.5B)",
    "States revenue as $30B+ (within +/- $0.5B)",
    "States thirteen stores with revenue $30.8B (within +/- $0.5B)",
    "States growth as 12 percent (within +/- 1 percent)",
    "States the spread as 425 bps (within +/- 1%)",
    "States net income as $3.2M in the red (within +/- $0.5M)",
    "States revenue as $30.8B " + "x" * 600 + " (within +/- $0.5B)",
    "States revenue as $30.8B (within +/- $0.5B) and more",
    # found by a third audit, after the rebuild as an allow-list: which number is the value?
    "States the Top 1,000 customers' average order as 1999 (within +/- 5)",
    "States the 12.5 mile route's total elevation gain as 2050 (within +/- 10)",
    "States the Windows 8.1 active installs as 1975 (within +/- 5)",
    "States the lease term as 10-year for 3,500 square feet (within +/- 1)",
    "States Fortune 500 respondents as a thousand (within +/- 50)",
    "States Form 10 filings received in May 25 (within +/- 2)",
    "States Boeing 737 deliveries in June 45 (within +/- 5)",
    "States Week 12 units shipped in June 30 (within +/- 2)",
    "States shares issued in June 12,500 (within +/- 100)",
    "States the Sept 30 headcount (within +/- 2)",
    # a scale that is there but not attached to the number
    "States total debt as $9,500,000 thousand, net (within +/- $50k)",
    "States shares outstanding as 153,000 thousand, diluted (within +/- 2k)",
    "States revenue as $120 million, up sharply (within +/- $5)",
    "States the backlog as $30 billion-plus (within +/- $1)",
    "States the loan sanctioned as 45 lacs (within +/- 2)",
    "States revenue in millions as $1,234 (within +/- $10)",
    "States net income in thousands as $16,183 (within +/- $200)",
    "States capex in $bn as 3.2 (within +/- 0.1)",
    # more one-sided and hedged wording, clock times, versions
    "States the headcount as 500 plus (within +/- 20)",
    "States a discount of upto 15% (within +/- 1 ppts)",
    "States revenue of at-least $5M (within +/- $0.5M)",
    "States revenue as est. $30.8B (within +/- $0.5B)",
    "States the stock of homes as 30 odd (within +/- 2)",
    "States the meeting start as 10.30 am (within +/- 0.15)",
    "States the departure as 1430 hours (within +/- 30)",
    "States the Python release as 3.11 (within +/- 0.01)",
    "States the low as 5 degrees subzero (within +/- 1)",
]


@pytest.mark.parametrize("text", HOSTILE)
def test_a_criterion_that_is_not_fully_understood_is_left_out(text):
    item, why = read_criterion(text)
    assert item is None and why, (text, item)


# Read, and read right: the value and tolerance a careful person would read.
READ_RIGHT = [
    ("States revenue as $30.8B (within +/- $500 MM)", "30800000000", "500000000", "USD"),
    ("States the index close as 2024.50 (within +/- 10)", "2024.50", "10", "count"),
    ("States FY2024 Q3 EPS as $2024 (within +/- $10)", "2024", "10", "USD"),
    ("States the exchange rate as 1.2024 (within +/- 0.005)", "1.2024", "0.005", "count"),
    ("States the price as $1.2025 (within +/- $0.01)", "1.2025", "0.01", "USD"),
    ("States June 30, 2025 unsecured term loans as $1,100,000 thousand (within +/- $5,000k)", "1100000000", "5000000", "USD"),
    ("States margin as 41.5% (within +/- 10 bps)", "41.5", "0.1", "percent"),
    ("States spread as 425 bps (within +/- 10 bps)", "4.25", "0.1", "percent"),
    ("States the sample mass as 5 kg (within +/- 0.1 kg)", "5", "0.1", "count"),
    ("States H2 output as 1,200 tonnes (within +/- 50 tonnes)", "1200", "50", "count"),
    ("States growth as +27% (within +/- 2 ppts)", "27", "2", "percent"),
    ("States leverage as 3.24x (within +/- 0.1x)", "3.24", "0.1", "count"),
    ("States salary as $85K (within +/- $2 K)", "85000", "2000", "USD"),
    ("States securities as 6,308,952 shares (within +/- 200k)", "6308952", "200000", "count"),
    ("States the rate as 5.5 % (within +/- 0.1 %)", "5.5", "0.1", "percent"),
]


@pytest.mark.parametrize("text,value,tolerance,unit", READ_RIGHT)
def test_what_is_read_is_read_right(text, value, tolerance, unit):
    item, why = read_criterion(text)
    assert why is None, (text, why)
    assert (Decimal(item["value"]), Decimal(item["tolerance"]), item["unit"]) == \
        (Decimal(value), Decimal(tolerance), unit)


def test_a_percent_tolerance_on_a_percentage_is_read_as_points_and_flagged(tmp_path):
    item, _ = read_criterion("States the rate as 5.31% (within +/- 0.1%)")
    assert item["tolerance"] == "0.1" and item["percent_tolerance_read_as_points"] is True
    item, _ = read_criterion("States the rate as 5.31% (within +/- 0.1 ppts)")
    assert "percent_tolerance_read_as_points" not in item
    r = scan_rubric(_write(tmp_path, "id,criterion\na,States the rate as 5.31% (within +/- 0.1%)\n"))
    assert r.counts["percent_tolerance_read_as_points"] == 1


def _one_number(sentence: str) -> Decimal:
    """Read the single number back out of a response, with a reader that shares no code
    with the package: digits, commas and a decimal point, then a scale suffix."""
    import re as _re
    found = _re.findall(r"(?<![\w.])\$?(\d[\d,]*(?:\.\d+)?)\s?(%|bps|thousand|million|billion|k|K|M|B)?(?![\w])", sentence)
    assert len(found) == 1, (sentence, found)
    digits, suffix = found[0]
    scale = {"": 1, "%": 1, "bps": Decimal("0.01"), "thousand": 10 ** 3, "k": 10 ** 3, "K": 10 ** 3,
             "million": 10 ** 6, "M": 10 ** 6, "billion": 10 ** 9, "B": 10 ** 9}[suffix]
    return Decimal(digits.replace(",", "")) * scale


def test_every_probe_states_the_value_it_claims_to_state(tmp_path):
    """The response sentence is re-read by a separate reader and compared with the value
    and the verdict the probe records."""
    rub = "id,criterion\n" + "\n".join(
        f'h{i},"{t}"' for i, (t, *_ ) in enumerate(READ_RIGHT)
        if not any(w in t for w in ("x (", "kg", "tonnes", "shares", "June", "FY2024", "H2"))) + "\n"
    r = scan_rubric(_write(tmp_path, rub))
    rows, _, _ = build_probes(r.receipt, ["0", "+0.5", "+0.9", "+1", "+1.1", "+2", "-0.9", "-1", "-1.1", "far", "+1.1u"])
    assert len(rows) > 60
    for p in rows:
        got = _one_number(p["response"])
        assert got == Decimal(p["stated_value"]), p
        ref, tol = Decimal(p["reference_value"]), Decimal(p["tolerance"])
        assert p["right_verdict"] == ("met" if abs(got - ref) <= tol else "unmet"), p
        if p["offset"] in ("+1", "-1"):
            assert p["right_verdict"] == "met"          # exactly on the edge is inside


def test_dates_and_period_labels_are_not_quantities():
    item, why = read_criterion("States FY2025 Q3 revenue at June 30 as $5,200 thousand (within +/- $50k)")
    assert why is None and item["value"] == "5200000" and item["tolerance"] == "50000"


def test_scan_counts_what_is_checkable_and_what_is_left_out(tmp_path):
    r = scan_rubric(_write(tmp_path, RUBRIC), where=["section=facts"])
    c = r.counts
    assert (c["criteria"], c["contain_within_plus_or_minus"], c["checkable"]) == (10, 9, 4)
    assert [i["id"] for i in r.items] == ["c1", "c2", "c3", "c6"]
    assert c["left_out"] == {"does_not_start_with_a_lead_word": 1,
                             "not_selected_or_not_a_positive_criterion": 2,
                             "tolerance_unit_differs": 1, "wording_not_read": 1}
    assert (c["groups"], c["groups_with_a_checkable_criterion"]) == (3, 2)
    # weight: checkable 10+5+5+6 = 26 of positive 10+5+5+8+4 + 6+3+2 + 7 = 50
    assert (c["weight"]["checkable"], c["weight"]["positive_total"]) == ("26", "50")
    assert r.receipt["receipt"] == CONTRACTS_SCHEMA


def test_a_second_lead_word_can_be_named(tmp_path):
    r = scan_rubric(_write(tmp_path, RUBRIC), lead=["States", "Reports"], where=["section=facts"])
    assert "c8" in [i["id"] for i in r.items]


def test_scan_refuses_an_unusable_rubric(tmp_path):
    with pytest.raises(InputError):
        scan_rubric(tmp_path / "missing.csv")
    with pytest.raises(InputError):
        scan_rubric(_write(tmp_path, "id,text\na,b\n"))
    with pytest.raises(InputError):
        scan_rubric(_write(tmp_path, "id,criterion\na,x\na,y\n"))
    with pytest.raises(InputError):
        scan_rubric(_write(tmp_path, RUBRIC), where=["nosuch=1"])


def test_probes_state_values_at_known_distances(tmp_path):
    r = scan_rubric(_write(tmp_path, RUBRIC), where=["section=facts"])
    rows, skipped, text = build_probes(r.receipt, ["0", "+0.5", "+0.9", "+1", "+1.1", "-1.1", "far", "+1.1u"])
    got = {x["probe_id"]: x for x in rows}
    assert got["c1@0"]["response"] == "Q3 revenue was $30.8B."
    assert got["c1@+0.9"]["response"] == "Q3 revenue was $31.25B."
    assert got["c1@+1.1"]["response"] == "Q3 revenue was $31.35B."
    assert got["c1@-1.1"]["response"] == "Q3 revenue was $30.25B."
    assert got["c1@+1.1u"]["response"] == "Q3 revenue was $31,350 million."
    assert got["c2@+1.1"]["response"] == "Headcount was 12,620 employees."
    assert got["c3@+1.1"]["response"] == "Gross margin was 42.05%."
    assert got["c6@-1.1"]["response"] == "The exam fee was $82."
    # the right verdict is arithmetic: inside up to and including the edge, outside beyond it
    assert [got[f"c1@{k}"]["right_verdict"] for k in ("0", "+0.5", "+0.9", "+1", "+1.1", "-1.1", "far")] == \
        ["met", "met", "met", "met", "unmet", "unmet", "unmet"]
    assert Decimal(got["c1@+1.1"]["stated_value"]) == Decimal("31350000000")
    # a count and a percentage have no other unit, and $104 cannot be written in thousands
    assert skipped == {"+1.1u:no_other_unit": 3}
    assert not {"c2@+1.1u", "c3@+1.1u", "c6@+1.1u"} & set(got)
    assert list(csv.DictReader(io.StringIO(text.split("\n", 1)[1])))[0]["probe_id"] == "c1@0"


def test_a_probe_that_would_not_be_positive_is_not_written(tmp_path):
    rub = _write(tmp_path, "id,criterion\nz,States the rate as 1% (within +/- 0.5 ppts)\n")
    rows, skipped, _ = build_probes(scan_rubric(rub).receipt, ["-1.1", "-2", "-3"])
    assert [r["probe_id"] for r in rows] == ["z@-1.1"] and rows[0]["response"] == "The rate was 0.45%."
    assert skipped == {"-2:value_not_positive": 1, "-3:value_not_positive": 1}


def test_unusable_offsets_are_refused(tmp_path):
    rec = scan_rubric(_write(tmp_path, RUBRIC)).receipt
    for bad in (["near"], ["0", "0"], [], ["faru"]):
        with pytest.raises(InputError):
            build_probes(rec, bad)


VERDICTS = """probe_id,call,context,verdict
c1@+1.1,0,,unmet
c1@+1.1,1,,unmet
c6@-1.1,0,,met
c6@-1.1,1,,met
c2@+1.1,0,,met
c2@+1.1,1,,unmet
c3@+1.1,0,,unmet
c1@+0.9,0,,met
c6@-1.1,0,report,unmet
"""


def _table(tmp_path):
    r = scan_rubric(_write(tmp_path, RUBRIC), where=["section=facts"])
    _, _, text = build_probes(r.receipt, ["+0.9", "+1.1", "-1.1"])
    probes = _write(tmp_path, text, "probes.csv")
    table, summary = probe_table(probes, _write(tmp_path, VERDICTS, "verdicts.csv"))
    return _write(tmp_path, table, "table.csv"), summary


def test_the_table_says_nothing_about_the_right_verdict(tmp_path):
    path, summary = _table(tmp_path)
    assert summary == {"rows": 9, "probes": 12, "probes_graded": 5, "probes_without_a_verdict": 7}
    header = path.read_text().splitlines()[1].split(",")
    assert "right_verdict" not in header and "response" not in header


def test_grader_check_counts_items_clusters_and_rounding(tmp_path):
    path, _ = _table(tmp_path)
    g = check_grader(path)
    s = g.summary
    assert (s["rows"], s["right"], s["lenient"], s["strict"]) == (9, 6, 3, 0)
    b = s["by_item"]["+1.1"]
    # three items at +1.1: c1 right twice, c2 accepted once of twice, c3 right
    assert (b["items"], b["wrong_at_least_once"], b["wrong_on_every_row"], b["rows_disagree"]) == (3, 1, 0, 1)
    assert (b["clusters"], b["clusters_with_a_wrong_item"]) == (1, 1)
    # c2: 12,620 against 12,400 +/- 200 is written at the criterion's precision and stays outside
    assert (b["lenient_items_at_reference_precision"], b["lenient_items_still_outside_after_rounding_half_up"],
            b["lenient_items_still_outside_after_rounding_toward_reference"],
            b["lenient_items_rounding_not_checked"]) == (1, 1, 1, 0)
    m = s["by_item"]["-1.1"]
    assert (m["items"], m["wrong_at_least_once"], m["wrong_on_every_row"]) == (1, 1, 1)
    assert m["lenient_items_still_outside_after_rounding_toward_reference"] == 1      # $82 against $83 to $103
    assert s["by_item"]["-1.1:report"]["wrong_at_least_once"] == 0   # a context is its own group
    assert verify(g.receipt, data=path).ok


def test_rounding_toward_the_reference_can_bring_a_value_onto_the_edge(tmp_path):
    rub = _write(tmp_path, "id,criterion\nd,States separation costs as $64M (within +/- $2M)\n")
    _, _, text = build_probes(scan_rubric(rub).receipt, ["+1.1"])
    table, _ = probe_table(_write(tmp_path, text, "p.csv"),
                           _write(tmp_path, "probe_id,verdict\nd@+1.1,met\n", "v.csv"))
    b = check_grader(_write(tmp_path, table, "t.csv")).summary["by_item"]["+1.1"]
    # $66.2M is outside $62M to $66M as written, but rounds to $66M at the criterion's precision
    assert (b["lenient_at_least_once"], b["lenient_items_at_reference_precision"],
            b["lenient_items_still_outside_after_rounding_half_up"],
            b["lenient_items_still_outside_after_rounding_toward_reference"]) == (1, 0, 0, 0)


def test_a_verdict_for_an_unknown_probe_is_refused(tmp_path):
    r = scan_rubric(_write(tmp_path, RUBRIC))
    _, _, text = build_probes(r.receipt, ["+1.1"])
    with pytest.raises(InputError):
        probe_table(_write(tmp_path, text, "p.csv"),
                    _write(tmp_path, "probe_id,verdict\nnope@+1.1,met\n", "v.csv"))


def test_the_contracts_file_is_a_receipt(tmp_path):
    rub = _write(tmp_path, RUBRIC)
    out = tmp_path / "contracts.json"
    out.write_text(json.dumps(scan_rubric(rub).receipt), encoding="utf-8")
    assert verify(out).ok
    rub.write_text(RUBRIC.replace("$30.8B", "$30.9B"), encoding="utf-8")
    v = verify(out)
    assert not v.ok and any(name == "rubric hash" and not ok for name, ok, _ in v.steps)


def test_command_line_from_rubric_to_report(tmp_path, capsys):
    rub = _write(tmp_path, RUBRIC)
    c, p, t = tmp_path / "contracts.json", tmp_path / "probes.csv", tmp_path / "table.csv"
    assert main(["scan", str(rub), "--where", "section=facts", "--out", str(c)]) == 0
    assert "checkable by rule:  4" in capsys.readouterr().out
    assert main(["probes", str(c), "--offsets", "+0.9,+1.1,-1.1", "--out", str(p),
                 "--receipt", str(tmp_path / "pr.json")]) == 0
    assert "probes:      12" in capsys.readouterr().out
    assert main(["verify", str(c)]) == 0 and main(["verify", str(tmp_path / "pr.json")]) == 0
    capsys.readouterr()
    assert main(["table", str(p), str(_write(tmp_path, VERDICTS, "v.csv")), "--out", str(t)]) == 0
    assert main(["check", str(t)]) == 1
    out = capsys.readouterr().out
    assert "by item" in out and "-1.1: 1 of 1 items wrong" in out
    assert main(["scan", str(tmp_path / "missing.csv")]) == 64


def test_the_published_study_is_rebuilt_from_its_criteria():
    """studies/judge-check-2026: from the 76 criterion texts alone, the same values and
    tolerances are read and every response the judge was sent is rebuilt byte for byte."""
    study = Path(__file__).resolve().parents[1] / "studies" / "judge-check-2026" / "results"
    if not study.is_dir():
        pytest.skip("the study folder is not in this checkout")
    old = json.loads((study / "draco_contracts" / "items.json").read_text())["items"]
    got = {}
    for it in old:
        item, why = read_criterion(it["requirement"])
        assert why is None, (it["item_id"], why)
        assert Decimal(item["value"]) == Decimal(it["num"].replace(",", "")) * Decimal(str(it["mult"]))
        assert float(item["tolerance"]) == pytest.approx(it["tolerance"], rel=1e-12)
        got[it["item_id"]] = dict(item, id=it["item_id"], group="", criterion=it["requirement"])
    rec = {"receipt": CONTRACTS_SCHEMA, "result": {"items": list(got.values())}}
    rows, _, _ = build_probes(rec, ["0", "+0.5", "+0.9", "+1.1", "+1.5", "+2", "-0.9", "-1.1",
                                    "far", "+0.9u", "+1.1u"])
    built = {(r["item"], r["offset"]): r for r in rows}
    stored = [(it["item_id"], lab, it["responses"][c]) for it in old
              for c, lab in (("exact", "0"), ("inside", "+0.5"), ("outside", "+2"), ("far", "far"))]
    names = {"near_inside": "+0.9", "near_outside": "+1.1", "units_inside": "+0.9u",
             "units_outside": "+1.1u", "below_outside": "-1.1", "below_inside": "-0.9",
             "above_150": "+1.5", "report_near_outside": "+1.1"}
    for f in ("draco_contracts/items_boundary.json", "draco_replication/items_replication.json"):
        for it in json.loads((study / f).read_text()):
            stored += [(it["item_id"], names[c], r) for c, r in it["responses"].items()]
    assert len(stored) == 849
    for item_id, label, r in stored:
        b = built[(item_id, label)]
        assert b["response"] == r["text"] and b["right_verdict"].upper() == r["expected"]


def test_the_published_study_comes_out_of_the_product_alone():
    """studies/judge-check-2026/results/draco_product: the probes, the judge's saved verdicts
    joined by `table`, decided by `check`. The files were written while these commands were
    part of the consilience package, so their first comment line names them as they were
    called there; with that line, this package rebuilds them byte for byte."""
    from consilience_judge_check.rubric import (PROBES_COMMENT_AS_FIRST_WRITTEN,
                                                TABLE_COMMENT_AS_FIRST_WRITTEN)
    d = Path(__file__).resolve().parents[1] / "studies" / "judge-check-2026" / "results" / "draco_product"
    if not d.is_dir():
        pytest.skip("the study folder is not in this checkout")
    assert verify(d / "probes_receipt.json").ok
    offsets = json.loads((d / "probes_receipt.json").read_text())["options"]["offsets"]
    _, _, probes_text = build_probes(d / "contracts.json", offsets,
                                     comment=PROBES_COMMENT_AS_FIRST_WRITTEN)
    assert probes_text.encode() == (d / "probes.csv").read_bytes()    # the preregistered file
    table, summary = probe_table(d / "probes.csv", d / "verdicts_saved.csv",
                                 comment=TABLE_COMMENT_AS_FIRST_WRITTEN)
    assert table.encode() == (d / "table_saved.csv").read_bytes() and summary["rows"] == 3051
    v = verify(d / "grader_receipt_saved.json")
    assert v.ok and v.command == "check"
    s = json.loads((d / "grader_receipt_saved.json").read_text())["result"]["summary"]
    assert (s["rows"], s["right"], s["lenient"], s["strict"], s["decided_exact"]) == (3051, 2872, 139, 40, 3051)
    b = s["by_item"]
    assert (b["-1.1"]["items"], b["-1.1"]["wrong_at_least_once"], b["-1.1"]["wrong_on_every_row"]) == (76, 22, 20)
    assert (b["+1.1"]["wrong_at_least_once"], b["+1.1:report"]["items"], b["+1.1:report"]["wrong_at_least_once"]) == (10, 69, 14)
    assert (b["-1.1"]["lenient_items_still_outside_after_rounding_half_up"],
            b["-1.1"]["lenient_items_still_outside_after_rounding_toward_reference"]) == (18, 17)
    assert (b["-1.1"]["clusters"], b["-1.1"]["clusters_with_a_wrong_item"], b["-1.1"]["largest_cluster"]) == \
        (10, 6, {"wrong": 15, "items": 39})
    assert b["0"]["wrong_at_least_once"] == 0 and b["far"]["wrong_at_least_once"] == 0


def test_probes_and_tables_refuse_what_they_cannot_use(tmp_path):
    rec = scan_rubric(_write(tmp_path, RUBRIC)).receipt
    for bad in (["NaN"], ["Infinity"], ["1e400"], ["sNaN"], ["+1.1x"], ["99999"]):
        with pytest.raises(InputError):
            build_probes(rec, bad)
    for damaged in ([], {"receipt": CONTRACTS_SCHEMA}, {"receipt": CONTRACTS_SCHEMA, "result": {"items": [{"id": "a"}]}}):
        with pytest.raises(InputError):
            build_probes(damaged, ["+1.1"])
    with pytest.raises(InputError):
        scan_rubric(_write(tmp_path, "id,weight,criterion\na,NaN,States x as $5 (within +/- $1)\n", "w.csv"))
    _, _, text = build_probes(rec, ["+1.1"])
    probes = _write(tmp_path, text, "p.csv")
    with pytest.raises(InputError):        # a call label on one verdict of a probe and not on the other
        probe_table(probes, _write(tmp_path, "probe_id,call,verdict\nc1@+1.1,,met\nc1@+1.1,0,met\n", "v.csv"))
    with pytest.raises(InputError):        # the same call twice
        probe_table(probes, _write(tmp_path, "probe_id,call,verdict\nc1@+1.1,a,met\nc1@+1.1,a,met\n", "v2.csv"))


def test_verify_catches_an_edited_contracts_file_and_a_missing_probes_file(tmp_path, capsys):
    rub = _write(tmp_path, RUBRIC)
    c, p, pr = tmp_path / "contracts.json", tmp_path / "probes.csv", tmp_path / "pr.json"
    assert main(["scan", str(rub), "--out", str(c)]) == 0
    assert main(["probes", str(c), "--offsets", "+1.1", "--out", str(p), "--receipt", str(pr)]) == 0
    assert verify(pr).ok and verify(c).ok
    # edit the contracts file but leave its recorded hash alone
    doc = json.loads(c.read_text())
    doc["result"]["items"][0]["tolerance"] = "1"
    c.write_text(json.dumps(doc), encoding="utf-8")
    v = verify(pr)
    assert not v.ok and any(n == "contracts hash" and not ok for n, ok, _ in v.steps)
    assert not verify(c).ok
    # restore, then lose the probes file
    assert main(["scan", str(rub), "--out", str(c)]) == 0
    assert verify(pr).ok
    p.unlink()
    v = verify(pr)
    assert not v.ok and any(n == "probes file" and not ok for n, ok, _ in v.steps)
    # a damaged receipt is an input error, not a crash
    pr.write_text(json.dumps({"receipt": "consilience-rubric-probes/v1"}), encoding="utf-8")
    with pytest.raises(InputError):
        verify(pr)
    capsys.readouterr()


def test_command_line_errors_exit_64(tmp_path, capsys):
    rub = _write(tmp_path, RUBRIC)
    c = tmp_path / "contracts.json"
    assert main(["scan", str(rub), "--out", str(c)]) == 0
    assert main(["scan", str(rub), "--where", "nosuch"]) == 64
    assert main(["scan", str(rub), "--out", str(tmp_path / "no" / "dir.json")]) == 64
    assert main(["probes", str(tmp_path), "--out", str(tmp_path / "p.csv")]) == 64
    assert main(["probes", str(rub), "--out", str(tmp_path / "p.csv")]) == 64       # not JSON
    assert main(["probes", str(c), "--offsets", "", "--out", str(tmp_path / "p.csv")]) == 64
    assert main(["probes", str(c), "--offsets", "NaN", "--out", str(tmp_path / "p.csv")]) == 64
    assert main(["probes", str(c), "--out", str(tmp_path / "no" / "p.csv")]) == 64
    assert main(["table", str(c), str(rub), "--out", str(tmp_path / "t.csv")]) == 64
    assert "Traceback" not in capsys.readouterr().err


GC_HEADER = "id,reference_value,reference_unit,tolerance,stated_value,stated_unit,grader_verdict,group,item,cluster,reference_step\n"


def test_item_counting_does_not_merge_or_drop_silently(tmp_path):
    rows = [
        "a#0,100,USD,10 USD,112,USD,met,g,A,t1,1",          # lenient
        "a#1,100,USD,10 USD,112,USD,unmet,g,A,t2,1",        # the same item, named in a second cluster
        "b#0,100,USD,10 USD,112,USD,unmet,g,B,t2,1",
        "c#0,100,USD,10 USD,112,USD,met,g,,t1,1",           # no item: counted as a row only
        "d#0,100,USD,10 USD,112,USD,maybe,g,D,t1,1",        # unreadable verdict: item D has no decided row
    ]
    s = check_grader(_write(tmp_path, GC_HEADER + "\n".join(rows) + "\n", "t.csv")).summary
    b = s["by_item"]["g"]
    assert (b["items"], b["wrong_at_least_once"], b["rows_disagree"]) == (2, 1, 1)
    assert b["items_in_more_than_one_cluster"] == 1
    assert (b["clusters"], b["largest_cluster_is_tied"]) == (2, True)
    assert (s["rows_without_an_item"], s["items_with_no_decided_row"]) == (1, 1)


def test_rounding_is_reported_three_ways_and_unknown_is_not_counted_as_inside(tmp_path):
    rows = [
        "p#0,64000000,USD,2000000 USD,66200000,USD,met,g,P,t,1000000",     # rounds onto the edge
        "q#0,64000000,USD,2000000 USD,66900000,USD,met,g,Q,t,1000000",     # 67 half up; 66 toward
        "r#0,93,USD,10 USD,82,USD,met,g,R,t,1",                           # at precision, outside
        "s#0,64000000,USD,2000000 USD,66200000,USD,met,g,S,t,",           # no step: cannot be said
        "u#0,64000000,USD,2000000 USD,66200000,USD,met,g,U,t,abc",
    ]
    b = check_grader(_write(tmp_path, GC_HEADER + "\n".join(rows) + "\n", "t.csv")).summary["by_item"]["g"]
    assert b["lenient_at_least_once"] == 5
    assert (b["lenient_items_rounding_checked"], b["lenient_items_rounding_not_checked"]) == (3, 2)
    assert (b["lenient_items_at_reference_precision"], b["lenient_items_still_outside_after_rounding_half_up"],
            b["lenient_items_still_outside_after_rounding_toward_reference"]) == (1, 2, 1)


def test_a_table_with_no_rows_does_not_claim_agreement(tmp_path, capsys):
    assert main(["check", str(_write(tmp_path, GC_HEADER, "empty.csv"))]) == 0
    out = capsys.readouterr().out
    assert "nothing was checked" in out and "agrees with the arithmetic on every row" not in out


def test_arithmetic_is_exact_beyond_the_usual_28_digits(tmp_path):
    rub = _write(tmp_path, "id,criterion\nbig,States the count as 12345678901234567890 (within +/- 0.000000001)\n")
    rows, _, _ = build_probes(scan_rubric(rub).receipt, ["0", "+1", "+1.1", "-1.1"])
    got = {r["offset"]: r for r in rows}
    assert got["+1.1"]["stated_value"] == "12345678901234567890.0000000011"
    assert [got[k]["right_verdict"] for k in ("0", "+1", "+1.1", "-1.1")] == ["met", "met", "unmet", "unmet"]
    table, _ = probe_table(_write(tmp_path, _csv_of(rows), "p.csv"),
                           _write(tmp_path, "probe_id,verdict\nbig@+1.1,met\nbig@+1,met\n", "v.csv"))
    s = check_grader(_write(tmp_path, table, "t.csv")).summary
    assert (s["right"], s["lenient"]) == (1, 1)


def _csv_of(rows):
    from consilience_judge_check.rubric import PROBE_COLUMNS
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(PROBE_COLUMNS)
    for r in rows:
        w.writerow([r[c] for c in PROBE_COLUMNS])
    return buf.getvalue()


def test_an_edited_contracts_file_builds_no_probes(tmp_path):
    rec = scan_rubric(_write(tmp_path, RUBRIC)).receipt
    for field, value in (("tolerance", "1"), ("value", "NaN"), ("span", "ab"), ("step", "0")):
        doc = json.loads(json.dumps(rec))
        doc["result"]["items"][0][field] = value
        with pytest.raises(InputError):
            build_probes(doc, ["+1.1"])
    doc = json.loads(json.dumps(rec))
    del doc["result"]["items"][0]["written"]["unit_text"]
    with pytest.raises(InputError):
        build_probes(doc, ["+1.1"])


def test_a_probes_receipt_with_edited_counts_does_not_verify(tmp_path, capsys):
    from consilience.hashing import sha256_json
    rub = _write(tmp_path, RUBRIC)
    c, p, pr = tmp_path / "contracts.json", tmp_path / "probes.csv", tmp_path / "pr.json"
    assert main(["scan", str(rub), "--out", str(c), "--review", str(tmp_path / "review.csv")]) == 0
    assert "c1,States Q3 revenue as $30.8B" in (tmp_path / "review.csv").read_text()
    assert main(["probes", str(c), "--offsets", "+1.1", "--out", str(p), "--receipt", str(pr)]) == 0
    rec = json.loads(pr.read_text())
    rec["result"]["probes"] = 999
    rec["sha256"] = sha256_json({k: v for k, v in rec.items() if k != "sha256"})
    pr.write_text(json.dumps(rec), encoding="utf-8")
    assert not verify(pr).ok
    capsys.readouterr()
    with pytest.raises(InputError):        # the same probe twice in a probes file
        probe_table(_write(tmp_path, p.read_text() + p.read_text().splitlines()[2] + "\n", "dup.csv"),
                    _write(tmp_path, "probe_id,verdict\nc1@+1.1,met\n", "v.csv"))


def test_more_things_that_are_counted_and_not_merged(tmp_path, capsys):
    rows = [
        "a#0,100,USD,10 USD,112,USD,met,g,A,,1",            # no cluster named
        "b#0,100,USD,10 USD,112,USD,unmet,g,B,t1,1",
        "b#1,200,USD,10 USD,212,USD,unmet,g,B,t1,1",        # the same item label, another reference
        "b#1,200,USD,10 USD,212,USD,unmet,g,B,t1,1",        # the same id again
        "c#0,1e40,USD,10 USD,1e41,USD,met,g,C,t1,1",        # numbers too large for the exact path
    ]
    path = _write(tmp_path, GC_HEADER + "\n".join(rows) + "\n", "t.csv")
    s = check_grader(path).summary
    b = s["by_item"]["g"]
    assert (b["items"], b["items_without_a_cluster"], b["clusters"]) == (3, 1, 1)
    assert (s["items_with_more_than_one_reference"], s["rows_with_a_repeated_id"]) == (1, 1)
    assert b["lenient_items_rounding_not_checked"] == 1      # the 1e40 row: decided, rounding not checked
    assert main(["check", str(path), "--receipt", str(tmp_path / "no" / "r.json")]) == 64
    capsys.readouterr()
    assert main(["check", str(path)]) == 1
    out = capsys.readouterr().out
    assert "different references" in out and "repeat an id" in out and "name no cluster" in out
    with pytest.raises(InputError):
        scan_rubric(_write(tmp_path, "id,weight,criterion\na,1e999999999,States x as $5 (within +/- $1)\n", "w.csv"))
