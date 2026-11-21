"""Two further arms for the DiscoverPhysics judge. See ../PREREGISTRATION_JUDGE_PANEL.md.

  panel    the 53 rule-written texts of judge_arm.py, scored by another judge model
  printed  the eleven explanations printed in the paper, re-scored by the default judge

Usage (through with_usage.py so token use is recorded):
  python pilot/with_usage.py USAGE.jsonl pilot/judge_panel.py panel --judge-model ID --out results/judge_panel/NAME.jsonl
  python pilot/with_usage.py USAGE.jsonl pilot/judge_panel.py printed --out results/judge_panel/printed.jsonl
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "adapters"))
import judge_arm  # noqa: E402  (the first arm's texts and call loop, unchanged)


def printed(out_path, repeats):
    worlds, evaluator = judge_arm._benchmark()
    judge = evaluator.ExplanationJudge()
    data = json.load(open(os.path.join(HERE, "paper_examples.json"), encoding="utf-8"))
    done = set()
    if os.path.exists(out_path):
        done = {(r["world"], r["repeat"]) for r in map(json.loads, open(out_path))}
    with open(out_path, "a") as f:
        for ex in data["examples"]:
            cfg = worlds.WORLDS[ex["world"]]
            for k in range(repeats):
                if (ex["world"], k) in done:
                    continue
                res = judge.score(ex["explanation"], cfg["optimal_explanation"],
                                  cfg.get("explanation_rubric"), verbose=False)
                f.write(json.dumps({"world": ex["world"], "repeat": k, "judge_model": judge.judge_model,
                                    "printed_raw_score": ex["printed_judge_raw_score"],
                                    "raw_score": res.get("raw_score"), "error": res.get("error"),
                                    "reasoning": res.get("reasoning")}, sort_keys=True) + "\n")
                f.flush()
                print(f"{ex['world']:<17}#{k} printed {ex['printed_judge_raw_score']} now {res.get('raw_score')}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("panel"); p.add_argument("--judge-model", required=True); p.add_argument("--out", required=True)
    p.add_argument("--repeats", type=int, default=5)
    q = sub.add_parser("printed"); q.add_argument("--out", required=True); q.add_argument("--repeats", type=int, default=5)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.cmd == "panel":
        judge_arm.run(a.repeats, a.judge_model, a.out)
    else:
        printed(a.out, a.repeats)
