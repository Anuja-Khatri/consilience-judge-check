"""`check`: a grader's verdicts against the engine's `compare`, where the right answer is
arithmetic. Every disagreement is named lenient or strict with a row receipt; every row
that cannot be decided is reported and counted, never guessed. All data here is made up."""

from __future__ import annotations

import json

import pytest

from consilience_judge_check import check_grader, verify
from consilience_judge_check.cli import main
from consilience.compare import InputError
from consilience_judge_check.grader import GRADER_RECEIPT_SCHEMA
from consilience.hashing import sha256_json

HEADER = "id,reference_value,reference_unit,tolerance,stated_value,stated_unit,grader_verdict,group\n"
ROWS = [
    # inside the tolerance, grader says met: right
    "a1,30800000000,USD,500000000 USD,31050000000,USD,met,inside",
    # outside the tolerance, grader says unmet: right
    "a2,30800000000,USD,500000000 USD,31800000000,USD,unmet,outside",
    # outside the tolerance, grader says met: lenient
    "a3,64000000,USD,2000000 USD,66200000,USD,MET,outside",
    # inside the tolerance, grader says unmet: strict
    "a4,19.67,USD,0.50 USD,20.12,USD,unmet,inside",
    # a bare tolerance is in the reference unit; percent
    "a5,5.31,percent,0.1,5.40,percent,pass,inside",
    # a count
    "a6,705593,count,15000,735593,count,fail,outside",
]


def _table(tmp_path, rows=ROWS, header=HEADER, name="cases.csv"):
    p = tmp_path / name
    p.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    return p


def test_right_lenient_and_strict_are_counted(tmp_path):
    g = check_grader(_table(tmp_path))
    s = g.summary
    assert (s["rows"], s["decided"], s["right"], s["lenient"], s["strict"]) == (6, 6, 4, 1, 1)
    assert s["undecided"] == 0 and s["grader_unreadable"] == 0
    kinds = {d["id"]: d["kind"] for d in g.disagreements}
    assert kinds == {"a3": "lenient", "a4": "strict"}
    assert g.exit_code == 1


def test_a_disagreement_carries_what_was_compared_and_a_row_receipt(tmp_path):
    g = check_grader(_table(tmp_path))
    d = next(x for x in g.disagreements if x["id"] == "a3")
    assert d["engine_verdict"] == "disagree" and d["grader_verdict"] == "met"
    assert d["stated"] == "66200000 USD" and d["reference"] == "64000000 USD"
    assert d["difference"] == pytest.approx(2200000) and d["difference_unit"] == "USD"
    assert len(d["row_sha256"]) == 64 and d["line"] == 4


def test_counts_by_group(tmp_path):
    g = check_grader(_table(tmp_path))
    by = g.summary["by_group"]
    assert by["inside"] == {"rows": 3, "decided": 3, "right": 2, "lenient": 0, "strict": 1,
                            "grader_unreadable": 0, "undecided": 0}
    assert by["outside"]["lenient"] == 1 and by["outside"]["right"] == 2


def test_all_right_exits_clean(tmp_path):
    g = check_grader(_table(tmp_path, rows=[ROWS[0], ROWS[1], ROWS[4], ROWS[5]]))
    assert g.exit_code == 0 and not g.disagreements


@pytest.mark.parametrize("row,reason", [
    # two currencies are two kinds of quantity: no exchange rate is assumed
    ("b1,100,USD,5 USD,101,EUR,met,x", "not_comparable"),
    # a unit that is not a unit
    ("b2,100,USD,5 USD,101,dollars,met,x", "unparseable"),
    # no tolerance stated
    ("b3,100,USD,,101,USD,met,x", "not_stated(tolerance)"),
    # a tolerance in another kind of quantity
    ("b4,100,USD,5 percent,101,USD,met,x", "unusable_input"),
    # a value that is not a number
    ("b5,about 100,USD,5 USD,101,USD,met,x", "unparseable"),
])
def test_rows_that_cannot_be_decided_are_reported_not_guessed(tmp_path, row, reason):
    g = check_grader(_table(tmp_path, rows=[ROWS[0], row]))
    assert g.summary["decided"] == 1 and g.summary["undecided"] == 1
    assert g.undecided[0]["reason"].startswith(reason)
    assert g.exit_code == 3


def test_an_unreadable_grader_verdict_is_reported(tmp_path):
    g = check_grader(_table(tmp_path, rows=["c1,100,USD,5 USD,101,USD,probably,x"]))
    assert g.summary["grader_unreadable"] == 1 and g.summary["decided"] == 0
    assert g.undecided[0]["reason"] == "grader_verdict_unreadable"
    assert g.exit_code == 3


def test_a_short_row_is_reported(tmp_path):
    g = check_grader(_table(tmp_path, rows=[ROWS[0], "d1,100,USD"]))
    assert g.undecided[0]["reason"] == "row_length" and g.exit_code == 3


def test_missing_column_and_missing_file_are_input_errors(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("id,reference_value\n1,2\n", encoding="utf-8")
    with pytest.raises(InputError, match="needed"):
        check_grader(p)
    with pytest.raises(InputError, match="not found"):
        check_grader(tmp_path / "absent.csv")


def test_the_group_column_is_optional(tmp_path):
    header = HEADER.replace(",group", "")
    rows = [r.rsplit(",", 1)[0] for r in ROWS]
    g = check_grader(_table(tmp_path, rows=rows, header=header))
    assert "by_group" not in g.summary and g.summary["lenient"] == 1


def test_receipt_hashes_its_contents_and_verifies(tmp_path):
    p = _table(tmp_path)
    g = check_grader(p)
    rec = g.receipt
    assert rec["receipt"] == GRADER_RECEIPT_SCHEMA and rec["command"] == "grader-check"   # the name the receipt format gives it
    assert rec["sha256"] == sha256_json({k: v for k, v in rec.items() if k != "sha256"})
    v = verify(rec)
    assert v.ok and v.command == "check" and v.recomputed_sha256 == rec["sha256"]


def test_verify_catches_a_changed_table_and_an_edited_receipt(tmp_path):
    p = _table(tmp_path)
    rec = check_grader(p).receipt
    edited = json.loads(json.dumps(rec))
    edited["result"]["summary"]["lenient"] = 0
    assert not verify(edited).ok
    p.write_text(p.read_text().replace("a3,64000000,USD,2000000 USD,66200000,USD,MET",
                                       "a3,64000000,USD,2000000 USD,66200000,USD,unmet"))
    v = verify(rec)
    assert not v.ok and [s[0] for s in v.steps if not s[1]] == ["data hash", "re-run"]


def test_same_table_same_receipt(tmp_path):
    p = _table(tmp_path)
    assert check_grader(p).receipt["sha256"] == check_grader(p).receipt["sha256"]


def test_command_line(tmp_path, capsys):
    p = _table(tmp_path)
    out = tmp_path / "receipt.json"
    assert main(["check", str(p), "--receipt", str(out)]) == 1
    text = capsys.readouterr().out
    assert "lenient:     1" in text and "strict:      1" in text and "a3" in text
    assert main(["verify", str(out)]) == 0
    assert "ok" in capsys.readouterr().out
    assert main(["check", str(tmp_path / "absent.csv")]) == 64


def test_currency_codes_are_units_of_their_own_kind(tmp_path):
    """This package teaches the engine five currency codes. An amount in one is not
    comparable with an amount in another, and a code takes no prefix wherever the engine
    reads a unit: in a unit cell, inside a value cell, in a tolerance however it is spaced."""
    import consilience_judge_check  # noqa: F401  (teaches the engine the codes)
    from consilience.compare import compare
    assert compare({"value": 100, "unit": "USD"}, {"value": 100, "unit": "USD"}).verdict == "agree"
    assert compare({"value": 100, "unit": "USD"},
                   {"value": 100, "unit": "EUR"}).verdict.startswith("not_comparable")
    assert compare({"value": 100, "unit": "USD"},
                   {"value": 100, "unit": "kUSD"}).verdict.startswith("unparseable")
    p = tmp_path / "t.csv"
    p.write_text("id,reference_value,reference_unit,tolerance,stated_value,stated_unit,grader_verdict\n"
                 "stated,100,USD,5 USD,101,kUSD,met\n"            # a prefix on the stated unit
                 "unitcell,30,kUSD,1000 USD,32000,USD,met\n"      # on the reference unit
                 "space,100000,USD,500 kUSD,700000,USD,met\n"     # in the tolerance
                 "glued,100000,USD,500kUSD,700000,USD,met\n"      # ... with no space
                 "tab,100000,USD,500\tkUSD,700000,USD,met\n"      # ... after a tab
                 "inline,30 kUSD,,1000 USD,32000,USD,met\n"       # inside a value cell
                 "other,100,EUR,5 EUR,101,MEUR,met\n"             # another code, another prefix
                 "plain,100,USD,5 USD,101,USD,met\n", encoding="utf-8")
    g = check_grader(p)
    assert [u["id"] for u in g.undecided] == ["stated", "unitcell", "space", "glued", "tab", "inline", "other"]
    assert all(u["reason"].startswith(("unparseable", "unusable_input")) for u in g.undecided)
    assert g.summary["decided"] == 1 and g.summary["right"] == 1


def test_a_receipt_is_found_beside_its_table_from_any_folder(tmp_path, monkeypatch):
    """A receipt records the table's path as it was given. `verify` also looks for a file
    of that name beside the receipt, and checks it by hash, so a study folder verifies
    from anywhere."""
    d = tmp_path / "study"
    d.mkdir()
    (d / "t.csv").write_text("id,reference_value,reference_unit,tolerance,stated_value,stated_unit,grader_verdict\n"
                             "a,100,USD,5 USD,101,USD,met\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["check", "study/t.csv", "--receipt", "study/r.json"]) == 0
    monkeypatch.chdir(d)
    assert verify(d / "r.json").ok
    monkeypatch.chdir(tmp_path.parent)
    assert verify(d / "r.json").ok
    (d / "t.csv").write_text("changed", encoding="utf-8")
    assert not verify(d / "r.json").ok


def test_version_fields_of_a_receipt(tmp_path):
    """A receipt written before this package had its own version number has no
    `judge_check_version` and still verifies. One with no engine version does not."""
    p = tmp_path / "t.csv"
    p.write_text("id,reference_value,reference_unit,tolerance,stated_value,stated_unit,grader_verdict\n"
                 "a,100,USD,5 USD,101,USD,met\n", encoding="utf-8")
    rec = check_grader(p).receipt
    assert rec["judge_check_version"] and rec["consilience_version"]
    def rehash(r):
        r = {k: v for k, v in r.items() if k != "sha256"}
        r["sha256"] = sha256_json(r)
        return r
    assert verify(rehash({k: v for k, v in rec.items() if k != "judge_check_version"})).ok
    assert not verify(rehash({k: v for k, v in rec.items() if k != "consilience_version"})).ok


def test_same_unit_rows_are_decided_in_exact_decimal_arithmetic(tmp_path):
    """Found by an independent audit: floating point with a relative guard called a value
    50 dollars past the edge of a half-billion tolerance 'inside'. Same-unit rows are now
    decided on the digits as written."""
    rows = [
        # 50 dollars past the edge: outside. A grader that rejects it is right.
        "e1,65600000000,USD,500000000 USD,66100000050,USD,unmet,",
        # the same value accepted: lenient
        "e2,65600000000,USD,500000000 USD,66100000050,USD,met,",
        # exactly on the edge: inside (5.41 - 5.31 is not exactly 0.1 in floating point)
        "e3,5.31,percent,0.1 percent,5.41,percent,met,",
        "e4,5.31,percent,0.1 percent,5.41,percent,unmet,",
        # one unit of the last digit past the edge
        "e5,5.31,percent,0.1 percent,5.4100000001,percent,unmet,",
    ]
    g = check_grader(_table(tmp_path, rows))
    s = g.summary
    assert (s["decided"], s["right"], s["lenient"], s["strict"]) == (5, 3, 1, 1)
    assert (s["decided_exact"], s["decided_float"]) == (5, 0)
    kinds = {d["id"]: (d["kind"], d["method"]) for d in g.disagreements}
    assert kinds == {"e2": ("lenient", "exact"), "e4": ("strict", "exact")}


def test_across_units_a_value_at_the_edge_is_left_undecided(tmp_path):
    rows = [
        # 110 cm against 1 m with 0.1 m allowed: exactly on the edge, after a conversion
        "u1,1,m,0.1 m,110,cm,met,",
        # clearly inside and clearly outside after a conversion: decided in floating point
        "u2,1,m,0.1 m,105,cm,met,",
        "u3,1,m,0.1 m,125,cm,met,",
    ]
    g = check_grader(_table(tmp_path, rows))
    s = g.summary
    assert (s["decided"], s["undecided"], s["right"], s["lenient"]) == (2, 1, 1, 1)
    assert (s["decided_exact"], s["decided_float"]) == (0, 2)
    assert [(u["id"], u["reason"]) for u in g.undecided] == [("u1", "at_the_edge")]
    assert g.exit_code == 3
    assert g.disagreements[0]["id"] == "u3" and g.disagreements[0]["method"] == "float"


def test_the_published_study_receipts_still_verify():
    """studies/judge-check-2026: the receipts re-run to the published counts."""
    from pathlib import Path
    study = Path(__file__).resolve().parents[1] / "studies" / "judge-check-2026" / "results"
    if not study.is_dir():
        pytest.skip("the study folder is not in this checkout")
    g = verify(study / "draco_contracts" / "grader_receipt.json")
    assert g.ok and g.command == "check"
    rec = json.loads((study / "draco_contracts" / "grader_receipt.json").read_text())
    s = rec["result"]["summary"]
    assert (s["rows"], s["right"], s["lenient"], s["strict"]) == (2298, 2218, 57, 23)
    assert (s["decided_exact"], s["decided_float"], s["undecided"]) == (2298, 0, 0)
    assert s["by_group"]["near_outside"]["lenient"] == 26
    r = verify(study / "draco_replication" / "grader_receipt.json")
    assert r.ok and r.command == "check"
    s = json.loads((study / "draco_replication" / "grader_receipt.json").read_text())["result"]["summary"]
    assert (s["rows"], s["right"], s["lenient"], s["strict"]) == (753, 654, 82, 17)
    assert (s["decided_exact"], s["decided_float"], s["undecided"]) == (753, 0, 0)
    assert s["by_group"]["below_outside"]["lenient"] == 63
    w = verify(study / "judge_panel" / "wrong_law_receipt.json")
    assert w.ok and w.command == "consilience check"      # the engine's own receipt, handed on


def test_the_reasoning_experiment_receipts_still_verify():
    """studies/judge-check-2026, Part 1c: the third judge with its reasoning switched on, and
    the control. The receipts re-run to the published counts."""
    from pathlib import Path
    d = Path(__file__).resolve().parents[1] / "studies" / "judge-check-2026" / "results" / "draco_reasoning"
    if not d.is_dir():
        pytest.skip("the study folder is not in this checkout")
    on = verify(d / "receipt_reasoning_on.json")
    off = verify(d / "receipt_reasoning_off_default_temperature.json")
    assert on.ok and off.ok
    s = json.loads((d / "receipt_reasoning_on.json").read_text())["result"]["summary"]
    assert (s["rows"], s["right"], s["lenient"], s["strict"], s["undecided"]) == (152, 151, 1, 0, 0)
    b = s["by_item"]
    assert (b["-1.1"]["items"], b["-1.1"]["wrong_at_least_once"]) == (76, 0)
    assert (b["+1.1"]["items"], b["+1.1"]["wrong_at_least_once"]) == (76, 1)
    s = json.loads((d / "receipt_reasoning_off_default_temperature.json").read_text())["result"]["summary"]
    assert (s["rows"], s["right"], s["lenient"], s["strict"], s["undecided"]) == (76, 52, 24, 0, 0)
    assert (s["by_item"]["-1.1"]["items"], s["by_item"]["-1.1"]["wrong_at_least_once"]) == (76, 24)
    assert s["by_item"]["-1.1"]["clusters_with_a_wrong_item"] == 7

