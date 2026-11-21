"""The DRACO known-answer test on the paper's third judge, with its reasoning switched on.

The DRACO paper runs its third judge with reasoning disabled and temperature 0. With those
settings it accepted a value just outside a criterion's stated tolerance for 27 of 76
criteria. This script puts the same sentences to the same judge in two other settings, to
see whether a reasoning step removes the error:

  reasoning_on                        the provider's reasoning switched on, at the smallest
                                      budget it allows. The provider does not accept
                                      temperature 0 together with reasoning, so this arm runs
                                      at the default temperature.
  reasoning_off_default_temperature   reasoning off, default temperature. The control: it
                                      shows what the change of temperature does by itself.

The cases are the probes that the tool built from DRACO's rubric
(results/draco_product/probes.csv), the grading prompt is the one printed in the DRACO paper,
and the verdicts go through `consilience-judge-check table` and `check`, which decide every
row. See ../PREREGISTRATION_DRACO_REASONING.md, written and committed before any call of the
run.

  ping      two calls on probes that are not part of the run (3 tolerances out), to learn
            the reply format and the cost of a call with reasoning on
  run       the staged run; resumable; stops when the metered spend reaches --cap
  verdicts  judge_calls.jsonl -> one verdicts file per arm, for `consilience-judge-check table`

Needs DRACO_HOME (the dataset's test.jsonl and the paper's TeX as draco_paper.tex) and the
judge's key in ANTHROPIC_API_KEY for the one command.
"""
from __future__ import annotations

import argparse, concurrent.futures, csv, hashlib, json, os, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draco_contracts as dc  # noqa: E402

ROOT = os.path.dirname(HERE)
PRODUCT = os.path.join(ROOT, "results", "draco_product")
OUT = os.path.join(ROOT, "results", "draco_reasoning")
PRICE_IN, PRICE_OUT = 3.00 / 1e6, 15.00 / 1e6      # US dollars per token; output includes reasoning

# What is sent besides the prompt. The arms differ in these settings only: the reasoning
# setting, and the larger reply limit that goes with it. (Corrected after the run: the
# comment used to say nothing else differed, which left out the reply limit.)
ARMS = {
    "reasoning_on": {"max_tokens": 2048, "thinking": {"type": "enabled", "budget_tokens": 1024}},
    "reasoning_off_default_temperature": {"max_tokens": 1024},
}
# (stage, arm, offset). Order is fixed; see the preregistration.
STAGES = [
    (1, "reasoning_on", "-1.1"),
    (2, "reasoning_off_default_temperature", "-1.1"),
    (3, "reasoning_on", "+1.1"),
]
_lock = threading.Lock()


def probes():
    lines = [l for l in open(os.path.join(PRODUCT, "probes.csv"), encoding="utf-8") if not l.startswith("#")]
    return {r["probe_id"]: r for r in csv.DictReader(lines)}


def plan(only_ping=False):
    ps = probes()
    items = sorted({p["item"] for p in ps.values()})
    if only_ping:
        return [(0, "reasoning_on", ps[f"{i}@+3"]) for i in items[:2]]
    return [(stage, arm, ps[f"{i}@{off}"]) for stage, arm, off in STAGES for i in items]


def run(model: str, cap: float, workers: int, only_ping=False):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "pings.jsonl" if only_ping else "judge_calls.jsonl")
    by_task = {t["id"]: t for t in dc.tasks()}
    system = dc.judge_system_prompt()
    client = dc._client(True)          # the same API version as the paper-settings arm
    done_rows = dc._read(path)
    done = {(r["arm"], r["probe_id"], r["call"]) for r in done_rows if r.get("error") is None}
    spent = [sum(r.get("cost_usd") or 0 for r in done_rows)]
    stop = [None]
    todo = [c for c in plan(only_ping) if (c[1], c[2]["probe_id"], 0) not in done]
    print(f"{len(todo)} calls planned; {spent[0]:.4f} US dollars already metered; cap {cap}", flush=True)

    def one(c):
        stage, arm, p = c
        with _lock:
            if stop[0] or spent[0] >= cap:
                stop[0] = stop[0] or f"cap of {cap} US dollars reached"
                return
        user = dc.judge_user_prompt(p["criterion"], 1, by_task[p["cluster"]]["problem"], p["response"])
        t0 = time.time()
        row = {"stage": stage, "arm": arm, "probe_id": p["probe_id"], "item": p["item"],
               "task_id": p["cluster"], "offset": p["offset"], "call": 0, "judge_model": model,
               "settings": ARMS[arm], "response_sha256": hashlib.sha256(p["response"].encode()).hexdigest()}
        try:
            msg = client.messages.create(model=model, system=system,
                                         messages=[{"role": "user", "content": user}], **ARMS[arm])
            text = "".join(b.text for b in msg.content if b.type == "text")
            reasoning = "".join((getattr(b, "thinking", "") or "") for b in msg.content if b.type == "thinking")
            cost = msg.usage.input_tokens * PRICE_IN + msg.usage.output_tokens * PRICE_OUT
            row.update(verdict=dc.parse_verdict(text), reply=text, reasoning=reasoning,
                       input_tokens=msg.usage.input_tokens, output_tokens=msg.usage.output_tokens,
                       stop_reason=msg.stop_reason, cost_usd=round(cost, 6), error=None)
            with _lock:
                spent[0] += cost
        except Exception as e:  # a failed call is recorded, never dropped
            row.update(verdict=None, reply=None, reasoning=None, cost_usd=0.0,
                       error=f"{type(e).__name__}: {e}"[:400])
        row["seconds"] = round(time.time() - t0, 2)
        dc._append(path, row)

    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        for i, _ in enumerate(ex.map(one, todo)):
            if i % 38 == 0:
                print(f"  {i}/{len(todo)}  metered {spent[0]:.3f} US dollars", flush=True)
    print(f"metered spend {spent[0]:.4f} US dollars. " + (f"Stopped: {stop[0]}." if stop[0] else "All planned calls made."))


def verdicts():
    allr = dc._read(os.path.join(OUT, "judge_calls.jsonl"))
    for arm in ARMS:
        rows = [r for r in allr if r["arm"] == arm and r.get("verdict")]
        with open(os.path.join(OUT, f"verdicts_{arm}.csv"), "w", newline="", encoding="utf-8") as f:
            f.write(f"# The judge's verdicts on the tool's probes, arm {arm}, one row per call.\n")
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["probe_id", "call", "context", "verdict"])
            for r in sorted(rows, key=lambda r: r["probe_id"]):
                w.writerow([r["probe_id"], r["call"], "", r["verdict"].lower()])
    by_stage = {}
    for r in allr:
        a = by_stage.setdefault(str(r["stage"]), {"arm": r["arm"], "offset": r["offset"], "calls": 0,
                                                  "with_a_verdict": 0, "failed_or_unreadable": 0,
                                                  "output_tokens": 0})
        a["calls"] += 1
        a["with_a_verdict" if r.get("verdict") else "failed_or_unreadable"] += 1
        a["output_tokens"] += r.get("output_tokens") or 0
    summary = {"calls": len(allr), "planned_per_stage": 76, "made_by_stage": by_stage,
               "metered_spend_usd": round(sum(r.get("cost_usd") or 0 for r in allr), 4),
               "judge_models": sorted({r["judge_model"] for r in allr}), "arms": ARMS}
    json.dump(summary, open(os.path.join(OUT, "run_summary.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("ping", "run"):
        s = sub.add_parser(name)
        s.add_argument("--model", required=True)
        s.add_argument("--cap", type=float, default=2.00)
        s.add_argument("--workers", type=int, default=4)
    sub.add_parser("verdicts")
    a = ap.parse_args()
    if a.cmd == "verdicts":
        verdicts()
    else:
        run(a.model, a.cap, a.workers, only_ping=(a.cmd == "ping"))
