"""Run another script with the token use of every model call written to a file.

Changes nothing about what is sent or returned: it wraps the benchmark's own
client function and records the model, the token counts and the time taken.
The key is never read here, printed or written.

Usage: python pilot/with_usage.py USAGE.jsonl SCRIPT.py [args...]
"""
import json, os, runpy, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "adapters"))
import discoverphysics as dp  # noqa: E402

usage_path, script = sys.argv[1], sys.argv[2]
dp._import()
from scienceagent import llm_client  # noqa: E402
import anthropic  # noqa: E402

_orig_create = anthropic.resources.messages.Messages.create


def _create(self, *a, **k):
    t0 = time.time()
    resp = _orig_create(self, *a, **k)
    u = resp.usage
    with open(usage_path, "a") as f:
        f.write(json.dumps({"model": k.get("model"), "input_tokens": u.input_tokens,
                            "output_tokens": u.output_tokens,
                            "stop_reason": resp.stop_reason,
                            "seconds": round(time.time() - t0, 2), "tag": os.environ.get("USAGE_TAG")}) + "\n")
    return resp


anthropic.resources.messages.Messages.create = _create
sys.argv = [script] + sys.argv[3:]
runpy.run_path(script, run_name="__main__")
