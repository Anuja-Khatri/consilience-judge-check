"""Checks on the DRACO tolerance results that were NOT preregistered.

They were added after an independent audit of the study (20 Nov 2026) and after the
replication arm had been read, to answer three objections a careful reader would raise.
They make no model call. Everything here is recomputed from the committed call records.

  1. Rounding. A value 1.1 tolerances from the reference is, for some criteria, less than
     one displayed digit past the edge. Would rounding the stated value to the criterion's
     own precision bring it inside? Counted under half-up rounding and under rounding
     toward the reference (the most favourable to the judge).
  2. Clustering. The 76 criteria come from 10 tasks, and one task holds half of them.
     Counts per task, the rate without the largest task, and an interval from resampling
     whole tasks.
  3. Reply against status. Replies whose explanation says the opposite of the status
     field, among the calls scored as right.

Usage: python pilot/draco_robustness.py   (writes results/draco_replication/robustness.json)
"""
from __future__ import annotations

import json, os, random, re
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP

import draco_contracts as dc
import draco_replication as dr

OUTSIDE = {  # condition -> (which record, arm)
    "near_outside": "first", "bare_outside": "first", "units_outside": "first", "report_outside": "first",
    "below_outside": "replication", "above_150": "replication", "report_near_outside": "replication",
}


def _decimals(num: str) -> int:
    return len(num.split(".")[1]) if "." in num else 0


def rounding(it: dict, text: str) -> dict:
    """The stated value in the criterion's own unit, rounded to the criterion's own decimals."""
    V, T = dc.exact_reference(it)
    mult = Decimal(str(it["mult"]))
    stated = dc.exact_stated(text)
    q = stated / mult                      # in the unit the criterion is written in
    step = Decimal(1).scaleb(-_decimals(it["num"]))
    half_up = q.quantize(step, rounding=ROUND_HALF_UP) * mult
    toward = q.quantize(step, rounding=ROUND_DOWN if stated > V else ROUND_UP) * mult
    extra_digits = max(0, -q.normalize().as_tuple().exponent) > _decimals(it["num"])
    return {"extra_digits": extra_digits,
            "outside_as_written": abs(stated - V) > T,
            "outside_after_half_up": abs(half_up - V) > T,
            "outside_after_rounding_toward_reference": abs(toward - V) > T}


def main():
    items = {i["item_id"]: i for i in json.load(open(os.path.join(dr.FIRST, "items.json"), encoding="utf-8"))["items"]}
    boundary = {r["item_id"]: r["responses"] for r in json.load(open(os.path.join(dr.FIRST, "items_boundary.json"), encoding="utf-8"))}
    repl = {r["item_id"]: r["responses"] for r in json.load(open(os.path.join(dr.OUT, "items_replication.json"), encoding="utf-8"))}
    first = dc._read(os.path.join(dr.FIRST, "judge_calls.jsonl"))
    second = dc._read(os.path.join(dr.OUT, "judge_calls.jsonl"))
    alone_met = {r["item_id"] for r in first if r["condition"] == "report_alone" and r["verdict"] == "MET"}
    first = [r for r in first if not (r["condition"].startswith("report_") and r["item_id"] in alone_met)]

    def text_of(r):
        c, i = r["condition"], r["item_id"]
        if c in repl.get(i, {}):
            return repl[i][c]["text"]
        if c in boundary.get(i, {}):
            return boundary[i][c]["text"]
        return items[i]["responses"][c.replace("bare_", "").replace("report_", "")]["text"]

    out = {"note": "Not preregistered. Added after the audit and after the replication arm was read.",
           "rounding": {}, "tasks": {}, "reply_against_status": {}}

    # 1. rounding
    for cond, arm in OUTSIDE.items():
        rows = [r for r in (first if arm == "first" else second) if r["condition"] == cond and r["verdict"] is not None]
        crit = sorted({r["item_id"] for r in rows})
        wrong = sorted({r["item_id"] for r in rows if r["verdict"] != r["expected"]})
        info = {i: rounding(items[i], text_of(next(r for r in rows if r["item_id"] == i))) for i in crit}
        assert all(v["outside_as_written"] for v in info.values())
        out["rounding"][cond] = {
            "criteria": len(crit), "accepted_at_least_once": len(wrong),
            "of_those_written_at_the_criterions_own_precision": sum(not info[i]["extra_digits"] for i in wrong),
            "of_those_still_outside_after_half_up_rounding": sum(info[i]["outside_after_half_up"] for i in wrong),
            "of_those_still_outside_after_rounding_toward_the_reference":
                sum(info[i]["outside_after_rounding_toward_reference"] for i in wrong),
            "all_criteria_still_outside_after_rounding_toward_the_reference":
                sum(v["outside_after_rounding_toward_reference"] for v in info.values()),
            "accepted_and_still_outside_after_rounding_toward_the_reference":
                sorted(i for i in wrong if info[i]["outside_after_rounding_toward_reference"]),
        }

    # 2. clustering by task
    task_of = {i: it["task_id"] for i, it in items.items()}
    sizes = {}
    for i, t in task_of.items():
        sizes[t] = sizes.get(t, 0) + 1
    biggest = max(sizes, key=sizes.get)
    out["tasks"]["criteria_per_task"] = sorted(sizes.values(), reverse=True)
    rng = random.Random(20261120)
    for cond, arm in OUTSIDE.items():
        if cond in ("units_outside",):
            continue
        rows = [r for r in (first if arm == "first" else second) if r["condition"] == cond and r["verdict"] is not None]
        crit = sorted({r["item_id"] for r in rows})
        wrong = {r["item_id"] for r in rows if r["verdict"] != r["expected"]}
        per = {}
        for i in crit:
            a = per.setdefault(task_of[i], [0, 0]); a[1] += 1; a[0] += i in wrong
        tasks = sorted(per)
        draws = []
        for _ in range(10000):
            pick = [per[rng.choice(tasks)] for _ in tasks]
            n = sum(p[1] for p in pick)
            draws.append(sum(p[0] for p in pick) / n)
        draws.sort()
        rest = [per[t] for t in tasks if t != biggest]
        out["tasks"][cond] = {
            "per_task_wrong_of_criteria": sorted(([w, n] for w, n in per.values()), key=lambda x: -x[1]),
            "tasks": len(tasks), "tasks_with_a_wrong_criterion": sum(w > 0 for w, _ in per.values()),
            "largest_task": per.get(biggest), "without_the_largest_task": [sum(w for w, _ in rest), sum(n for _, n in rest)],
            "criteria_rate": round(len(wrong) / len(crit), 4),
            "interval_criteria_independent": dc.wilson(len(wrong), len(crit)),
            "interval_resampling_tasks": [round(draws[249], 4), round(draws[9749], 4)],
        }

    # 3. replies whose explanation says the opposite of the status, among calls scored as right
    says_in = re.compile(r"falls within|is within|within the acceptable|satisf", re.I)
    says_out = re.compile(r"outside|exceed|not within|does not|doesn't|beyond|not satisf|unmet|fails", re.I)
    for name, rows in (("first_arms", first), ("replication_arm", second)):
        hits = []
        for r in rows:
            if r["verdict"] is None or r["verdict"] != r["expected"] or r["condition"] == "report_alone":
                continue
            m = re.search(r'"explanation"\s*:\s*"(.*?)"\s*,\s*"criterion_status"', r["reply"] or "", re.S)
            e = m.group(1) if m else (r["reply"] or "")
            if r["verdict"] == "UNMET" and says_in.search(e) and not says_out.search(e):
                hits.append(f'{r["item_id"]}_{r["condition"]}_{r["repeat"]}')
            if r["verdict"] == "MET" and says_out.search(e) and not says_in.search(e):
                hits.append(f'{r["item_id"]}_{r["condition"]}_{r["repeat"]}')
        out["reply_against_status"][name] = {"calls_scored_right": sum(
            r["verdict"] is not None and r["verdict"] == r["expected"] and r["condition"] != "report_alone" for r in rows),
            "explanation_says_the_opposite": sorted(hits)}

    # how many criteria in the benchmark state a tolerance, by wording
    n_within = n_any = 0
    t_any = set()
    for t in dc.tasks():
        for sec in t["rubric"]["sections"]:
            for c in sec["criteria"]:
                if re.search(r"within\s*\+/-|±", c["requirement"]):
                    n_within += 1
                if re.search(r"\+/-|±", c["requirement"]):
                    n_any += 1; t_any.add(t["id"])
    out["tolerance_criteria_in_benchmark"] = {"wording_within_plus_minus": n_within, "any_plus_minus": n_any,
                                              "tasks_with_any": len(t_any)}
    json.dump(out, open(os.path.join(dr.OUT, "robustness.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
