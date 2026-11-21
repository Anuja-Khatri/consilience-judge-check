"""Adapter for the DiscoverPhysics benchmark (MIT licence, SampsonML/DiscoverPhysics).

Nothing from the benchmark is copied here. Point DISCOVERPHYSICS_HOME at a
clone of the repository; this module imports its simulator and evaluator.

What the adapter provides:
  reference_law(world)   the simulator itself, wrapped as a law, so the
                         reference card is measured, never hand-written
  tested_range(world)    the part of input space the benchmark's held-out
                         trajectory cases actually visit
  trajectory_score(...)  the benchmark's own trajectory test and pass rule
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from contextlib import redirect_stdout

import numpy as np

TWO_BODY_WORLDS = ("gravity", "yukawa", "fractional", "coulomb_easy",
                   "extra_dimensions", "oscillator")
PASS_NORMALISED_MSE = 0.1  # the benchmark's trajectory pass rule (paper and code agree)


def _home() -> str:
    home = os.environ.get("DISCOVERPHYSICS_HOME")
    if not home or not os.path.isdir(os.path.join(home, "ScienceAgent")):
        raise RuntimeError("set DISCOVERPHYSICS_HOME to a clone of SampsonML/DiscoverPhysics")
    return home


def _import():
    home = _home()
    for sub in ("ScienceAgent", "PhysicsSchool", "scripts"):
        p = os.path.join(home, sub)
        if p not in sys.path:
            sys.path.insert(0, p)
    from scienceagent import worlds, evaluator  # noqa: F401
    return worlds, evaluator


def benchmark_commit() -> str:
    head = os.path.join(_home(), ".git", "HEAD")
    try:
        ref = open(head).read().strip()
        if ref.startswith("ref:"):
            ref = open(os.path.join(_home(), ".git", ref.split()[1])).read().strip()
        return ref[:12]
    except OSError:
        return "unknown"


def world_variance(world: str) -> float:
    """Per-world trajectory variance the benchmark divides the MSE by."""
    src = open(os.path.join(_home(), "scripts", "run_benchmark.py")).read()
    block = src[src.index("_WORLD_VARS"):]
    block = block[block.index("{") + 1: block.index("}")]
    table = {}
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":")
            table[k.strip().strip('"')] = float(v.strip().rstrip(","))
    return table[world]


class ExecutorLaw:
    """The benchmark's simulator for one world, answering the law interface."""

    def __init__(self, world: str, engine: str = "nbody"):
        worlds, _ = _import()
        self.world = world
        self._cfg = worlds.get_world(world, engine=engine)
        self._ex = self._cfg["executor"]
        desc = json.dumps({"world": world, "engine": engine,
                           "kwargs": worlds.WORLDS[world].get("executor_kwargs", {}),
                           "commit": benchmark_commit()}, sort_keys=True, default=str)
        self.identity = "discoverphysics:" + world + ":" + hashlib.sha256(desc.encode()).hexdigest()[:16]

    def batch(self, calls):
        out = []
        for pos1, pos2, p1, p2, v2, dur in calls:
            try:
                rel = [pos2[0] - pos1[0], pos2[1] - pos1[1]]
                with self._ex.noise_disabled():
                    res = self._ex.run([{"p1": float(p1), "p2": float(p2), "pos2": rel,
                                         "velocity2": list(v2),
                                         "measurement_times": [float(dur)]}])[0]
                p = res["pos2"][-1]; v = res["velocity2"][-1]
                out.append({"ok": True, "pos": [p[0] + pos1[0], p[1] + pos1[1]],
                            "vel": [float(v[0]), float(v[1])]})
            except Exception as e:
                out.append({"ok": False, "error": f"{type(e).__name__}: {e}"[:200]})
        return out


    def trajectories(self, experiments):
        """One simulation per experiment, all measurement times at once."""
        out = []
        for e in experiments:
            try:
                with self._ex.noise_disabled():
                    res = self._ex.run([{"p1": float(e["p1"]), "p2": float(e["p2"]),
                                         "pos2": list(e["pos2"]),
                                         "velocity2": list(e["velocity2"]),
                                         "measurement_times": list(e["measurement_times"])}])[0]
                pos = [[float(p[0]), float(p[1])] for p in res["pos2"]]
                out.append(pos if len(pos) == len(e["measurement_times"])
                           and all(np.isfinite(pos).ravel()) else None)
            except Exception:
                out.append(None)
        return out


def noise_sigma(world: str, noise_frac: float = 0.05) -> float:
    """Position noise the benchmark adds: a fraction of the per-world spread."""
    return noise_frac * world_variance(world) ** 0.5


def test_cases(world: str):
    worlds, evaluator = _import()
    cfg = worlds.get_world(world, engine="nbody")
    ev_cls = cfg.get("evaluator_class") or evaluator.Evaluator
    ev = ev_cls(cfg["executor"])
    return ev, list(ev.test_cases)


def tested_range(world: str):
    """Range of separation, parameters and time the held-out cases visit."""
    from consilience_laws import TestedRange

    ev, cases = test_cases(world)
    with ev.executor.noise_disabled():
        truth = ev.executor.run(cases)
    rs = []
    for case, gt in zip(cases, truth):
        rs.append(float(np.linalg.norm(case["pos2"])))
        for p1, p2 in zip(gt["pos1"], gt["pos2"]):
            rs.append(float(np.linalg.norm(np.asarray(p2) - np.asarray(p1))))
    return TestedRange(
        r_min=min(rs), r_max=max(rs),
        p1_min=min(c["p1"] for c in cases), p1_max=max(c["p1"] for c in cases),
        p2_min=min(c["p2"] for c in cases), p2_max=max(c["p2"] for c in cases),
        t_max=max(max(c["measurement_times"]) for c in cases),
    )


def trajectory_score(world: str, law_source: str) -> dict:
    """Run the benchmark's own trajectory test on a law source."""
    ev, _ = test_cases(world)
    buf = io.StringIO()
    with redirect_stdout(buf):
        res = ev.evaluate(law_source, verbose=False)
    mse = float(res["mean_pos_error"])
    norm = mse / world_variance(world)
    return {"mean_pos_error": mse, "normalised_mse": norm,
            "passes_trajectory_test": bool(np.isfinite(norm) and norm < PASS_NORMALISED_MSE)}
