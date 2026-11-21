"""Turn the DRACO judge calls into the table that `consilience grader-check` reads.

One row per judge call whose right verdict is fixed by the rubric's stated tolerance:
the value the criterion names, its tolerance, the value the graded response states, and
the judge's verdict. Amounts are written in full (dollars, percent, plain counts) so the
Consilience engine decides each row itself; nothing here says what the right verdict is.

Every number in the table is exact: the reference and tolerance are read from the
criterion's own digits and the stated value is read back out of the response sentence,
all in decimal arithmetic, and written out in full.

Left out: the report-alone calls (a guard, not a test), and the in-report calls of the
three criteria the judge had already called MET on the report alone, because there a
MET cannot be laid to the inserted sentence. (Read afterwards: in one of the three the
report did state the figure; in the other two the judge's MET on the report alone was
itself wrong. See the study's write-up.)

Usage: python pilot/draco_grader_table.py
Then:  consilience grader-check results/draco_contracts/grader_table.csv \
           --receipt results/draco_contracts/grader_receipt.json
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draco_contracts as dc  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "draco_contracts")
UNIT = {"money": "USD", "percent": "percent", "count": "count"}


def main():
    items = {i["item_id"]: i for i in json.load(open(os.path.join(OUT, "items.json"), encoding="utf-8"))["items"]}
    boundary = {r["item_id"]: r["responses"] for r in
                json.load(open(os.path.join(OUT, "items_boundary.json"), encoding="utf-8"))}
    calls = [json.loads(l) for l in open(os.path.join(OUT, "judge_calls.jsonl"), encoding="utf-8")]
    stated_twice = {c["item_id"] for c in calls if c["condition"] == "report_alone" and c["verdict"] == "MET"}
    rows, left_out = [], {"report_alone": 0, "judge_called_the_report_alone_MET": 0}
    for c in sorted(calls, key=lambda c: (c["condition"], c["item_id"], c["repeat"])):
        cond, it = c["condition"], items[c["item_id"]]
        if cond == "report_alone":
            left_out["report_alone"] += 1
            continue
        if cond.startswith("report_") and c["item_id"] in stated_twice:
            left_out["judge_called_the_report_alone_MET"] += 1
            continue
        key = cond.replace("bare_", "").replace("report_", "").replace("_note", "")
        resp = boundary[c["item_id"]].get(cond) or it["responses"][key]
        unit = UNIT[it["family"]]
        V, T = dc.exact_reference(it)
        stated = dc.exact_stated(resp["text"])
        assert float(V) == it["value"] or abs(float(V) - it["value"]) < 1e-6 * it["value"]
        assert abs(float(stated) - resp["value"]) <= 1e-9 * max(1.0, abs(resp["value"]))
        rows.append([f'{c["item_id"]}_{cond}_{c["repeat"]}', dc.plain(V), unit,
                     f'{dc.plain(T)} {unit}', dc.plain(stated), unit,
                     c["verdict"].lower(), cond])
    with open(os.path.join(OUT, "grader_table.csv"), "w", newline="", encoding="utf-8") as f:
        f.write("# DRACO tolerance criteria: one row per judge call. Built by pilot/draco_grader_table.py\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "reference_value", "reference_unit", "tolerance", "stated_value", "stated_unit",
                    "grader_verdict", "group"])
        w.writerows(rows)
    print(len(rows), "rows;", "left out:", left_out)


if __name__ == "__main__":
    main()
