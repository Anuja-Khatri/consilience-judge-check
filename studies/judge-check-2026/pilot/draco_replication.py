"""Replication arm for the DRACO tolerance study: new responses, same judge, same prompt.

The first near-boundary arm (PREREGISTRATION_DRACO_BOUNDARY.md) was designed after the
first results were read, tested values above the reference only, and used single
sentences only. This arm tests the same question on responses the judge has not been
shown: values below the reference, a value further out, and the near-boundary value
placed inside a long report. See ../PREREGISTRATION_DRACO_REPLICATION.md, written and
committed before any call in this arm.

  items      build the new responses by rule and check them by separate arithmetic; no model call
  judge      call the judge on every (item, condition, repeat); resumable
  summarise  counts by criterion and by task, and the table for `consilience grader-check`

Nothing in the first arms' folder is written to: this arm keeps its own call record in
results/draco_replication/.
"""
from __future__ import annotations

import argparse, concurrent.futures, csv, hashlib, json, os, re, time
from decimal import Decimal

import draco_contracts as dc

FIRST = dc.OUT
OUT = os.path.join(dc.ROOT, "results", "draco_replication")

# name: (offset in tolerances, right verdict, placed inside the long report, calls per item)
CONDITIONS = {
    "below_outside": ("-1.1", "UNMET", False, 3),
    "below_inside": ("-0.9", "MET", False, 3),
    "above_150": ("1.5", "UNMET", False, 3),
    "report_near_outside": ("1.1", "UNMET", True, 1),
}
UNIT = {"money": "USD", "percent": "percent", "count": "count"}


def _exact(it):
    V = Decimal(it["num"].replace(",", "")) * Decimal(str(it["mult"]))
    T = Decimal(str(it["tolerance"]))
    if T == T.to_integral_value():
        T = T.to_integral_value()
    return V, T


def _stated(text: str, it: dict) -> Decimal:
    """Read the number back out of a response sentence, independently of how it was written."""
    toks = list(dc.VALUE_TOKEN.finditer(dc._mask_dates(text)))
    assert len(toks) == 1, (text, [t.group(0) for t in toks])
    m = toks[0]
    unit = (m.group("unit") or "").strip().lower()
    mult = dc.PCT_UNITS[unit] if unit in dc.PCT_UNITS else dc.MONEY_MULT.get(unit, 1.0)
    return Decimal(m.group("num").replace(",", "")) * Decimal(str(mult))


def build():
    items = json.load(open(os.path.join(FIRST, "items.json"), encoding="utf-8"))["items"]
    reports = {r["task_id"]: r["text"] for r in dc._read(os.path.join(FIRST, "reports.jsonl"))}
    first = dc._read(os.path.join(FIRST, "judge_calls.jsonl"))
    # in-report items: the judge called the report alone UNMET in the first arm (the figure is not already there)
    alone_unmet = {r["item_id"] for r in first if r["condition"] == "report_alone" and r["verdict"] == "UNMET"}
    out, skipped, problems = [], {}, 0
    for it in items:
        V, T = _exact(it)
        rec = {"item_id": it["item_id"], "task_id": it["task_id"], "requirement": it["requirement"], "responses": {}}
        for cond, (k, expected, in_report, _) in CONDITIONS.items():
            v = V + Decimal(k) * T
            if v <= 0:
                skipped[cond + ":value_not_positive"] = skipped.get(cond + ":value_not_positive", 0) + 1
                continue
            sent = dc.sentence(it, v)
            # separate arithmetic: read the number back from the sentence and compare with V and T
            got = _stated(sent, it)
            right = "MET" if abs(got - V) <= T else "UNMET"
            if got != v or right != expected:
                problems += 1
            r = {"text": sent, "value": float(v), "expected": expected, "in_report": in_report}
            if in_report:
                rep = reports.get(it["task_id"])
                token = dc._fmt(v, it)
                if it["item_id"] not in alone_unmet:
                    skipped["report:no_report_or_report_already_states_the_figure"] = \
                        skipped.get("report:no_report_or_report_already_states_the_figure", 0) + 1
                    continue
                if token in rep or token.replace(",", "") in rep.replace(",", ""):
                    skipped["report:new_number_already_in_report"] = skipped.get("report:new_number_already_in_report", 0) + 1
                    continue
                r["response_sha256"] = hashlib.sha256(dc.insert(rep, sent).encode()).hexdigest()
            rec["responses"][cond] = r
        out.append(rec)
    return out, skipped, problems


def run_judge(model: str, workers: int):
    recs = json.load(open(os.path.join(OUT, "items_replication.json"), encoding="utf-8"))
    items = {it["item_id"]: it for it in json.load(open(os.path.join(FIRST, "items.json"), encoding="utf-8"))["items"]}
    reports = {r["task_id"]: r["text"] for r in dc._read(os.path.join(FIRST, "reports.jsonl"))}
    by_id = {t["id"]: t for t in dc.tasks()}
    system = dc.judge_system_prompt()
    path = os.path.join(OUT, "judge_calls.jsonl")
    done = {(r["item_id"], r["condition"], r["repeat"], r["judge_model"]) for r in dc._read(path) if r.get("error") is None}
    client = dc._client(True)  # the paper's setting for this judge: temperature 0
    todo = []
    for rec in recs:
        for cond, r in rec["responses"].items():
            for k in range(CONDITIONS[cond][3]):
                if (rec["item_id"], cond, k, model) not in done:
                    todo.append((rec, cond, k, r))
    print(f"{len(todo)} judge calls to make", flush=True)

    def one(c):
        rec, cond, k, r = c
        it = items[rec["item_id"]]
        response = dc.insert(reports[it["task_id"]], r["text"]) if r["in_report"] else r["text"]
        sha = hashlib.sha256(response.encode()).hexdigest()
        assert not r["in_report"] or sha == r["response_sha256"]
        user = dc.judge_user_prompt(it["requirement"], it["weight"], by_id[it["task_id"]]["problem"], response)
        t0 = time.time()
        row = {"item_id": it["item_id"], "task_id": it["task_id"], "criterion_id": it["criterion_id"],
               "condition": cond, "repeat": k, "expected": r["expected"], "judge_model": model,
               "temperature_zero": True, "response_sha256": sha}
        try:
            msg = client.messages.create(model=model, max_tokens=1024, system=system,
                                         messages=[{"role": "user", "content": user}],
                                         extra_body={"temperature": 0})
            text = "".join(b.text for b in msg.content if b.type == "text")
            row.update(verdict=dc.parse_verdict(text), reply=text, input_tokens=msg.usage.input_tokens,
                       output_tokens=msg.usage.output_tokens, stop_reason=msg.stop_reason, error=None)
        except Exception as e:  # a failed call is recorded, never dropped
            row.update(verdict=None, reply=None, error=f"{type(e).__name__}: {e}"[:300])
        row["seconds"] = round(time.time() - t0, 2)
        dc._append(path, row)

    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        for i, _ in enumerate(ex.map(one, todo)):
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


def _by_criterion(rows):
    """One condition's calls -> counts with the criterion, then the task, as the unit."""
    exp = rows[0]["expected"]
    per_item, task_of = {}, {}
    for r in rows:
        per_item.setdefault(r["item_id"], []).append(r["verdict"])
        task_of[r["item_id"]] = r["task_id"]
    wrong_items = sorted(i for i, vs in per_item.items() if any(v != exp for v in vs))
    n = len(per_item)
    return {"expected": exp, "calls": len(rows), "wrong_calls": sum(r["verdict"] != exp for r in rows),
            "criteria": n, "criteria_wrong_at_least_once": len(wrong_items),
            "criteria_wrong_on_every_call": sum(all(v != exp for v in vs) for vs in per_item.values()),
            "criteria_whose_repeats_disagree": sum(len(set(vs)) > 1 for vs in per_item.values()),
            "criteria_wrong_rate": round(len(wrong_items) / n, 4),
            "criteria_wrong_rate_95ci": dc.wilson(len(wrong_items), n),
            "tasks": len(set(task_of.values())), "tasks_with_a_wrong_criterion": len({task_of[i] for i in wrong_items}),
            "wrong_criteria": wrong_items}


def _own_range(reply: str, it: dict):
    """Does a reply write out both ends of the correct allowed range (value minus and plus tolerance)?
    Decided by rule: both numbers must appear in the reply, in the criterion's own unit."""
    V, T = _exact(it)
    mult = Decimal(str(it["mult"]))
    want = {((V - T) / mult).normalize(), ((V + T) / mult).normalize()}
    found = set()
    for tok in re.findall(r"\d[\d,]*(?:\.\d+)?", reply or ""):
        try:
            found.add(Decimal(tok.replace(",", "")).normalize())
        except Exception:
            pass
    return want <= found


def self_contradictions(rows, items):
    """Among wrong verdicts: how many replies state the correct range and still give the wrong verdict."""
    out = {}
    for r in rows:
        if r["verdict"] is None or r["verdict"] == r["expected"] or r["condition"] == "report_alone":
            continue
        a = out.setdefault(r["condition"], {"wrong_calls": 0, "reply_states_the_correct_range": 0, "other": []})
        a["wrong_calls"] += 1
        if _own_range(r["reply"], items[r["item_id"]]):
            a["reply_states_the_correct_range"] += 1
        else:
            a["other"].append(f'{r["item_id"]}_{r["repeat"]}')
    return out


def summarise():
    rows = dc._read(os.path.join(OUT, "judge_calls.jsonl"))
    first = dc._read(os.path.join(FIRST, "judge_calls.jsonl"))
    items = {it["item_id"]: it for it in json.load(open(os.path.join(FIRST, "items.json"), encoding="utf-8"))["items"]}
    recs = {r["item_id"]: r for r in json.load(open(os.path.join(OUT, "items_replication.json"), encoding="utf-8"))}
    ok = [r for r in rows if r["verdict"] is not None]
    out = {"calls": len(rows), "failed_or_unparsed_calls": len(rows) - len(ok),
           "judge_models": sorted({r["judge_model"] for r in rows}), "this_arm": {}, "first_arms_by_criterion": {}}
    for cond in CONDITIONS:
        rs = [r for r in ok if r["condition"] == cond]
        if rs:
            out["this_arm"][cond] = _by_criterion(rs)
    # the first arms' single-sentence conditions, recounted with the criterion as the unit
    for cond in ("bare_exact", "bare_inside", "near_inside", "near_outside", "bare_outside", "bare_far"):
        rs = [r for r in first if r["condition"] == cond and r["verdict"] is not None]
        out["first_arms_by_criterion"][cond] = _by_criterion(rs)
    # in-report, first arm, restricted as in its own report to items the judge called UNMET on the report alone
    alone_unmet = {r["item_id"] for r in first if r["condition"] == "report_alone" and r["verdict"] == "UNMET"}
    for cond in ("report_inside", "report_outside"):
        rs = [r for r in first if r["condition"] == cond and r["verdict"] is not None and r["item_id"] in alone_unmet]
        out["first_arms_by_criterion"][cond] = _by_criterion(rs)
    a = set(out["first_arms_by_criterion"]["near_outside"]["wrong_criteria"])
    b = set(out["this_arm"].get("below_outside", {}).get("wrong_criteria", []))
    out["just_outside_above_and_below"] = {"above_only": len(a - b), "below_only": len(b - a), "both": len(a & b),
                                           "either": len(a | b), "criteria": len(items),
                                           "either_rate_95ci": dc.wilson(len(a | b), len(items))}
    stated_twice = {r["item_id"] for r in first if r["condition"] == "report_alone" and r["verdict"] == "MET"}
    out["wrong_replies_this_arm"] = self_contradictions(rows, items)
    out["wrong_replies_first_arms"] = self_contradictions(
        [r for r in first if not (r["condition"].startswith("report_") and r["item_id"] in stated_twice)], items)
    out["tokens"] = {"input": sum(r.get("input_tokens") or 0 for r in rows),
                     "output": sum(r.get("output_tokens") or 0 for r in rows)}
    json.dump(out, open(os.path.join(OUT, "summary.json"), "w"), indent=1, sort_keys=True)

    with open(os.path.join(OUT, "grader_table.csv"), "w", newline="", encoding="utf-8") as f:
        f.write("# DRACO tolerance criteria, replication arm: one row per judge call. Built by pilot/draco_replication.py\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "reference_value", "reference_unit", "tolerance", "stated_value", "stated_unit",
                    "grader_verdict", "group"])
        for r in sorted(ok, key=lambda r: (r["condition"], r["item_id"], r["repeat"])):
            it, unit = items[r["item_id"]], UNIT[items[r["item_id"]]["family"]]
            V, T = dc.exact_reference(it)
            stated = dc.exact_stated(recs[r["item_id"]]["responses"][r["condition"]]["text"])
            w.writerow([f'{r["item_id"]}_{r["condition"]}_{r["repeat"]}', dc.plain(V), unit,
                        f'{dc.plain(T)} {unit}', dc.plain(stated), unit, r["verdict"].lower(), r["condition"]])
    print(json.dumps({k: v for k, v in out.items() if k != "first_arms_by_criterion"}, indent=1))
    print("first arms, by criterion:")
    for cond, s in out["first_arms_by_criterion"].items():
        print(f'  {cond:16s} wrong on {s["criteria_wrong_at_least_once"]:2d} of {s["criteria"]} criteria '
              f'({s["wrong_calls"]} of {s["calls"]} calls), in {s["tasks_with_a_wrong_criterion"]} of {s["tasks"]} tasks')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("items")
    j = sub.add_parser("judge"); j.add_argument("--model", required=True); j.add_argument("--workers", type=int, default=6)
    sub.add_parser("summarise")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.cmd == "items":
        recs, skipped, problems = build()
        json.dump(recs, open(os.path.join(OUT, "items_replication.json"), "w"), indent=1, ensure_ascii=False)
        n = {c: sum(c in r["responses"] for r in recs) for c in CONDITIONS}
        print(len(recs), "items;", n, "| left out:", skipped, "| arithmetic problems:", problems)
        print("calls planned:", sum(n[c] * CONDITIONS[c][3] for c in CONDITIONS))
    elif a.cmd == "judge":
        run_judge(a.model, a.workers)
    else:
        summarise()
