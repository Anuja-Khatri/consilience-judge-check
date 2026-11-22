"""The DRACO known-answer test on a judge from the benchmark's primary judge family.

The cases are the probes that `consilience rubric probes` builds from DRACO's rubric
(results/draco_product/probes.csv). This script only sends them to the judge, with the
grading prompt printed in the DRACO paper, and writes down what comes back. The verdicts
then go through `consilience rubric table` and `consilience grader-check`, which decide
every row. See ../PREREGISTRATION_DRACO_SECOND_JUDGE.md, written and committed before any call
of the run.

  ping      two calls on probes that are not part of the run (3 tolerances out), to
            learn the reply format and the cost of a call
  run       the staged run; resumable; stops when the metered spend reaches --cap
  verdicts  judge_calls.jsonl -> verdicts.csv, the file `consilience rubric table` reads

The key is never read here. Requests go through the session's proxy, which adds it; the
Authorization header below is a placeholder that the proxy replaces.

Needs DRACO_HOME (the dataset's test.jsonl and the paper's TeX as draco_paper.tex).
"""
from __future__ import annotations

import argparse, concurrent.futures, csv, hashlib, json, os, sys, threading, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draco_contracts as dc  # noqa: E402

ROOT = os.path.dirname(HERE)
PRODUCT = os.path.join(ROOT, "results", "draco_product")
OUT = os.path.join(ROOT, "results", "draco_second_judge")
FIRST = os.path.join(ROOT, "results", "draco_contracts")
REPL = os.path.join(ROOT, "results", "draco_replication")
URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
# the paper's settings for its primary judge: thinking level low, temperature 0.2
SETTINGS = {"temperature": 0.2, "reasoning_effort": "low", "max_tokens": 2048}
PRICE_IN, PRICE_OUT = 2.00 / 1e6, 12.00 / 1e6     # US dollars per token; output includes thinking

# (stage, offset, context, call numbers). Order is fixed; see the preregistration.
STAGES = [
    (1, ["-1.1", "+1.1"], "", [0]),
    (2, ["0", "far"], "", [0]),
    (3, ["+1.1"], "report", [0]),
    (4, ["-0.9", "+0.9"], "", [0]),
    (5, ["-1.1", "+1.1"], "", [1, 2]),
]
_lock = threading.Lock()
# The service allows this key 25 requests a minute for this model. Calls are started at
# most once every 2.7 seconds. Two changes were made to this script after the first calls
# of the run. After 25 records: this pacing, more attempts, and a narrower rule for when
# a refusal stops the run (the run had been stopped by the per-minute limit, which the
# first version took for a refusal to bill). After 247 records: the run stops at once on
# the provider's per-day limit. The stages, settings, prompts, verdict pattern and cap
# were not changed. (This comment was corrected on 22 Nov; it used to name one change.)
MIN_GAP = 2.7
_next_start = [0.0]


def _pace():
    with _lock:
        now = time.time()
        wait = max(0.0, _next_start[0] - now)
        _next_start[0] = max(now, _next_start[0]) + MIN_GAP
    if wait:
        time.sleep(wait)


def probes():
    lines = [l for l in open(os.path.join(PRODUCT, "probes.csv"), encoding="utf-8") if not l.startswith("#")]
    return {r["probe_id"]: r for r in csv.DictReader(lines)}


def report_items():
    """The 69 criteria used in a report in the replication arm, with the hash of the text sent."""
    recs = json.load(open(os.path.join(REPL, "items_replication.json"), encoding="utf-8"))
    return {r["item_id"]: r["responses"]["report_near_outside"]["response_sha256"]
            for r in recs if "report_near_outside" in r["responses"]}


def plan(only_ping=False):
    ps = probes()
    items = sorted({p["item"] for p in ps.values()})
    if only_ping:
        return [(0, ps[f"{i}@+3"], "", 0) for i in items[:2]]
    in_report = report_items()
    out = []
    for stage, offsets, context, calls in STAGES:
        for k in calls:
            for i in items:
                if context == "report" and i not in in_report:
                    continue
                for off in offsets:
                    out.append((stage, ps[f"{i}@{off}"], context, k))
    return out


def call_judge(model: str, system: str, user: str):
    body = dict(SETTINGS, model=model, messages=[{"role": "system", "content": system},
                                                 {"role": "user", "content": user}])
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": "Bearer proxy-injected"})
    last = None
    for attempt in range(7):
        _pace()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode()), None
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:400]
            last = f"HTTP {e.code}: {text}"
            if e.code == 429 and "per_day" in text:  # the day's allowance is used up: stop
                return None, last
            if e.code == 429:                       # over the per-minute limit: wait it out
                time.sleep(min(60, 20 * (attempt + 1)))
                continue
            if e.code in (500, 502, 503, 504):
                time.sleep(4 * (attempt + 1))
                continue
            return None, last
        except Exception as e:  # network trouble: try again
            last = f"{type(e).__name__}: {e}"[:300]
            time.sleep(4 * (attempt + 1))
    return None, last


def run(model: str, cap: float, workers: int, only_ping=False):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "pings.jsonl" if only_ping else "judge_calls.jsonl")
    by_task = {t["id"]: t for t in dc.tasks()}
    system = dc.judge_system_prompt()
    reports = {r["task_id"]: r["text"] for r in dc._read(os.path.join(FIRST, "reports.jsonl"))}
    in_report = report_items()
    done_rows = dc._read(path)
    done = {(r["probe_id"], r["context"], r["call"]) for r in done_rows if r.get("error") is None}
    spent = [sum(r.get("cost_usd") or 0 for r in done_rows)]
    stop = [None]
    todo = [c for c in plan(only_ping) if (c[1]["probe_id"], c[2], c[3]) not in done]
    print(f"{len(todo)} calls planned; {spent[0]:.4f} US dollars already metered; cap {cap}", flush=True)

    def one(c):
        stage, p, context, k = c
        with _lock:
            if stop[0] or spent[0] >= cap:
                stop[0] = stop[0] or f"cap of {cap} US dollars reached"
                return
        response = p["response"]
        if context == "report":
            response = dc.insert(reports[p["cluster"]], p["response"])
            assert hashlib.sha256(response.encode()).hexdigest() == in_report[p["item"]]
        user = dc.judge_user_prompt(p["criterion"], 1, by_task[p["cluster"]]["problem"], response)
        t0 = time.time()
        row = {"stage": stage, "probe_id": p["probe_id"], "item": p["item"], "task_id": p["cluster"],
               "offset": p["offset"], "context": context, "call": k, "judge_model": model,
               "settings": SETTINGS, "response_sha256": hashlib.sha256(response.encode()).hexdigest()}
        data, err = call_judge(model, system, user)
        if data is None:
            row.update(verdict=None, reply=None, error=err, cost_usd=0.0)
            if err and err.startswith("HTTP 4"):      # refused even after waiting: stop the run
                with _lock:
                    stop[0] = f"the service refused the call: {err[:160]}"
        else:
            ch = (data.get("choices") or [{}])[0]
            text = (ch.get("message") or {}).get("content") or ""
            u = data.get("usage") or {}
            pin, tot = u.get("prompt_tokens") or 0, u.get("total_tokens") or 0
            cost = pin * PRICE_IN + max(0, tot - pin) * PRICE_OUT
            row.update(verdict=dc.parse_verdict(text), reply=text, finish_reason=ch.get("finish_reason"),
                       usage=u, cost_usd=round(cost, 6), error=None)
            with _lock:
                spent[0] += cost
        row["seconds"] = round(time.time() - t0, 2)
        dc._append(path, row)

    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        for i, _ in enumerate(ex.map(one, todo)):
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}  metered {spent[0]:.3f} US dollars", flush=True)
    print(f"metered spend {spent[0]:.4f} US dollars. " + (f"Stopped: {stop[0]}." if stop[0] else "All planned calls made."))


def verdicts():
    rows = [r for r in dc._read(os.path.join(OUT, "judge_calls.jsonl")) if r.get("verdict")]
    with open(os.path.join(OUT, "verdicts.csv"), "w", newline="", encoding="utf-8") as f:
        f.write("# The judge's verdicts on the product's probes, one row per call.\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["probe_id", "call", "context", "verdict"])
        for r in sorted(rows, key=lambda r: (r["probe_id"], r["context"], r["call"])):
            w.writerow([r["probe_id"], r["call"], r["context"], r["verdict"].lower()])
    allr = dc._read(os.path.join(OUT, "judge_calls.jsonl"))
    by_stage = {}
    for r in allr:
        a = by_stage.setdefault(r["stage"], {"calls": 0, "with_a_verdict": 0, "failed_or_unreadable": 0})
        a["calls"] += 1
        a["with_a_verdict" if r.get("verdict") else "failed_or_unreadable"] += 1
    planned = {}
    for stage, *_ in plan():
        planned[stage] = planned.get(stage, 0) + 1
    summary = {"calls": len(allr), "planned_by_stage": planned, "made_by_stage": by_stage,
               "metered_spend_usd": round(sum(r.get("cost_usd") or 0 for r in allr), 4),
               "judge_models": sorted({r["judge_model"] for r in allr}), "settings": SETTINGS,
               "tokens": {"prompt": sum((r.get("usage") or {}).get("prompt_tokens") or 0 for r in allr),
                          "total": sum((r.get("usage") or {}).get("total_tokens") or 0 for r in allr)}}
    json.dump(summary, open(os.path.join(OUT, "run_summary.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("ping", "run"):
        s = sub.add_parser(name)
        s.add_argument("--model", required=True)
        s.add_argument("--cap", type=float, default=4.25)
        s.add_argument("--workers", type=int, default=4)
    sub.add_parser("verdicts")
    a = ap.parse_args()
    if a.cmd == "verdicts":
        verdicts()
    else:
        run(a.model, a.cap, a.workers, only_ping=(a.cmd == "ping"))
