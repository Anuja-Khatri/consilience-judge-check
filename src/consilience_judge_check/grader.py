"""``check``: where the right answer is arithmetic, is the grader right?

A grader (a person, a script or a language model) is often asked whether a stated value
matches a reference value within a tolerance that the rubric itself states. That is a
comparison of two quantities, with one right answer. ``check`` reads a table with
one row per graded case, decides each row, and reports where the grader's verdict
differs:

``lenient``  the grader accepted a value outside the stated tolerance
``strict``   the grader rejected a value inside the stated tolerance

How a row is decided. The Consilience engine's ``compare`` is run on every row, so units
are read and checked the same way as in the ``consilience`` package. Then:

* reference, stated value and tolerance all written in the same unit: the row is decided
  in exact decimal arithmetic on the digits as written (``method: exact``);
* a unit conversion is needed: ``compare``'s floating-point answer is used
  (``method: float``), unless the value lies within floating-point noise of the edge of
  the tolerance, in which case the row is left undecided (``at_the_edge``).

A row that cannot be decided (a unit that cannot be read, two different kinds of
quantity, a missing tolerance, a value at the edge across units) is reported with the
reason and counted. Nothing is guessed. The grader is never run here: the table holds
verdicts it already gave.

The table is a CSV file with a header row and these columns:

==================  ==================================================================
``id``              any label for the row
``reference_value`` the value the rubric names (a number)
``reference_unit``  its unit (for example ``USD``, ``percent``, ``count``)
``tolerance``       the stated tolerance, a quantity such as ``500000 USD``; a bare
                    number is in the reference unit
``stated_value``    the value in the graded response
``stated_unit``     its unit
``grader_verdict``  ``met`` or ``unmet`` (also pass/fail, yes/no, true/false, 1/0)
``group``           optional: a label to count by
``item``            optional: what the row is a case of (for example the criterion). When
                    one item is graded several times, the report also counts items: an
                    item is wrong if any of its rows is
``cluster``         optional, with ``item``: a label for items that belong together (for
                    example the task a criterion comes from)
``reference_step``  optional, with ``item``: one unit of the last digit the reference is
                    written to (1000000 for "$64M"). The report then says how many of
                    the accepted values are still outside the tolerance after rounding
                    to that precision, and after rounding toward the reference
==================  ==================================================================

The whole report is a receipt (``consilience-grader-receipt/v1``) that
``consilience-judge-check verify`` re-runs from the table. In the receipt, ``command`` keeps
the name the format has given this operation since its first version, ``grader-check``.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import math
import re
from decimal import (ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, DecimalException,
                     InvalidOperation, localcontext)
from pathlib import Path
from typing import Optional, Union

from consilience import __version__ as ENGINE_VERSION
from consilience.check import EXIT_CLEAN, EXIT_UNPARSEABLE, EXIT_VIOLATIONS, _read_table
from consilience.compare import PINT_VERSION, ROUNDING, InputError, compare
from consilience.hashing import sha256_bytes, sha256_json

from . import units as _units  # noqa: F401  (registers the currency codes with the engine)
from ._version import __version__

GRADER_RECEIPT_SCHEMA = "consilience-grader-receipt/v1"
REQUIRED_COLUMNS = ("id", "reference_value", "reference_unit", "tolerance", "stated_value",
                    "stated_unit", "grader_verdict")
MET_WORDS = frozenset({"met", "pass", "passed", "yes", "true", "1"})
UNMET_WORDS = frozenset({"unmet", "fail", "failed", "no", "false", "0"})
# compare's verdicts, read as the answer to "is the stated value within the tolerance?"
ENGINE_MET = ("agree", "within_floor")
ENGINE_UNMET = ("disagree",)
_COUNTS = ("rows", "decided", "right", "lenient", "strict", "grader_unreadable", "undecided")
# compare allows ROUNDING x the larger value for floating-point noise. Across units, a value
# this close to the edge of the tolerance is not decided here (a few times that allowance).
EDGE_GUARD = 4 * ROUNDING


@dataclass
class GraderResult:
    summary: dict
    disagreements: list
    undecided: list
    receipt: dict = field(repr=False)

    @property
    def exit_code(self) -> int:
        if self.summary["undecided"] or self.summary["grader_unreadable"]:
            return EXIT_UNPARSEABLE
        return EXIT_VIOLATIONS if self.disagreements else EXIT_CLEAN

    def to_dict(self) -> dict:
        return copy.deepcopy(self.receipt)


def _read_verdict(text: str) -> Optional[str]:
    t = text.strip().lower()
    if t in MET_WORDS:
        return "met"
    if t in UNMET_WORDS:
        return "unmet"
    return None


_PLAIN_NUMBER = re.compile(r"[+-]?(?=\d|\.\d)\d{0,30}(?:\.\d{0,30})?")


def _same_unit_numbers(row: dict):
    """(reference, stated, tolerance) as exact decimals when all three are written in
    one unit, else None."""
    unit = row["reference_unit"].strip()
    if row["stated_unit"].strip() != unit:
        return None
    parts = row["tolerance"].strip().split(None, 1)
    if len(parts) == 2 and parts[1].strip() != unit:
        return None
    cells = (row["reference_value"].strip(), row["stated_value"].strip(), parts[0] if parts else "")
    if not all(_PLAIN_NUMBER.fullmatch(c) for c in cells):
        return None                      # exponents, signs of infinity, 40-digit numbers: not here
    ref, stated, tol = (Decimal(c) for c in cells)
    return ref, stated, tol


def _rounding(row: dict):
    """For a same-unit row with a ``reference_step`` (one unit of the last digit the
    reference is written to): is the stated value written at that precision, is it still
    outside the tolerance after ordinary rounding to it (half up), and after rounding
    toward the reference (the reading most favourable to the grader)?
    Returns (at_precision, outside_half_up, outside_toward), or None when that cannot be
    said (no usable step, or a unit conversion would be needed)."""
    nums = _same_unit_numbers(row)
    cell = (row.get("reference_step") or "").strip()
    if nums is None or not _PLAIN_NUMBER.fullmatch(cell) or Decimal(cell) <= 0:
        return None
    ref, stated, tol = nums
    step = Decimal(cell)
    try:
        with localcontext() as ctx:
            ctx.prec = 100
            q = stated / step
            half_up = q.to_integral_value(rounding=ROUND_HALF_UP) * step
            if stated > ref:
                toward = max(q.to_integral_value(rounding=ROUND_FLOOR) * step, ref)
            else:
                toward = min(q.to_integral_value(rounding=ROUND_CEILING) * step, ref)
            return stated % step == 0, abs(half_up - ref) > tol, abs(toward - ref) > tol
    except DecimalException:
        return None


def _wilson(k: int, n: int, z: float = 1.96):
    """A 95% interval for k of n, treating the n as independent."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def _by_item(cases: dict, has_cluster: bool, has_step: bool) -> dict:
    """Counts with the item as the unit, per group. ``cases`` maps (group, item) to a
    dict with the outcomes of its decided rows, its clusters and its rounding flags."""
    out = {}
    for group in sorted({g for g, _ in cases}, key=lambda g: (g is None, g or "")):
        mine = {i: c for (g, i), c in cases.items() if g == group}
        wrong = {i for i, c in mine.items() if any(o != "right" for o in c["outcomes"])}
        lenient = {i for i, c in mine.items() if "lenient" in c["outcomes"]}
        e = {
            "items": len(mine), "wrong_at_least_once": len(wrong),
            "wrong_on_every_row": sum(all(o != "right" for o in c["outcomes"]) for c in mine.values()),
            "rows_disagree": sum(len(set(c["outcomes"])) > 1 for c in mine.values()),
            "lenient_at_least_once": len(lenient),
            "strict_at_least_once": sum("strict" in c["outcomes"] for c in mine.values()),
            "wrong_share_95": _wilson(len(wrong), len(mine)),
        }
        if has_cluster:
            per = {}
            for i, c in mine.items():
                if not c["clusters"]:
                    continue                                     # no cluster named: counted below
                a = per.setdefault(c["clusters"][0], [0, 0])     # an item counts in its first cluster
                a[1] += 1
                a[0] += i in wrong
            e["items_without_a_cluster"] = sum(not c["clusters"] for c in mine.values())
            if not per:
                per = {"": [0, 0]}
            top = max(n for _, n in per.values())
            tied = sorted(k for k in per if per[k][1] == top)
            big = tied[0]
            e.update(clusters=len(per), clusters_with_a_wrong_item=sum(w > 0 for w, _ in per.values()),
                     largest_cluster={"wrong": per[big][0], "items": per[big][1]},
                     largest_cluster_is_tied=len(tied) > 1,
                     other_clusters={"wrong": sum(w for k, (w, _) in per.items() if k != big),
                                     "items": sum(n for k, (_, n) in per.items() if k != big)},
                     items_in_more_than_one_cluster=sum(len(c["clusters"]) > 1 for c in mine.values()))
        if has_step:
            checked = [i for i in lenient if mine[i]["rounding"] is not None]
            e.update(
                lenient_items_rounding_checked=len(checked),
                lenient_items_rounding_not_checked=len(lenient) - len(checked),
                lenient_items_at_reference_precision=sum(mine[i]["rounding"][0] for i in checked),
                lenient_items_still_outside_after_rounding_half_up=sum(mine[i]["rounding"][1] for i in checked),
                lenient_items_still_outside_after_rounding_toward_reference=sum(
                    mine[i]["rounding"][2] for i in checked))
        out[group if group is not None else ""] = e
    return out


def _exact_same_unit(row: dict) -> Optional[str]:
    """'met' or 'unmet' by exact decimal arithmetic, when the reference, the stated value
    and the tolerance are all written in the same unit. None when that does not apply."""
    nums = _same_unit_numbers(row)
    if nums is None:
        return None
    ref, stated, tol = nums
    with localcontext() as ctx:
        ctx.prec = 100
        return "met" if abs(stated - ref) <= tol else "unmet"


def _decide(row: dict):
    """One row: ('met' | 'unmet' | None, verdict or reason, compare's result, method)."""
    tol = row["tolerance"].strip()
    if not tol:
        return None, "not_stated(tolerance)", None, None
    try:
        r = compare({"value": row["reference_value"].strip(), "unit": row["reference_unit"].strip()},
                    {"value": row["stated_value"].strip(), "unit": row["stated_unit"].strip()},
                    abs_tol=tol, precision="exact")
    except InputError as exc:
        return None, f"unusable_input({exc})", None, None
    base = r.verdict.split("(", 1)[0]
    if base not in ENGINE_MET and base not in ENGINE_UNMET:
        return None, r.verdict, r, None
    exact = _exact_same_unit(row)
    if exact is not None:
        return exact, ("agree" if exact == "met" else "disagree"), r, "exact"
    # a unit conversion was needed: floating point, so stay away from the edge
    if r.difference is not None and r.tolerance is not None:
        scale = abs(r.a["value"]) + abs(r.difference)
        if abs(r.difference - r.tolerance) <= EDGE_GUARD * scale:
            return None, "at_the_edge", r, None
    return ("met" if base in ENGINE_MET else "unmet"), r.verdict, r, "float"


def check_grader(data: Union[str, Path]) -> GraderResult:
    """Check the grader verdicts in the CSV file ``data`` against ``compare``.

    Raises ``InputError`` for a missing file, an unreadable CSV or a missing column.
    """
    p = Path(data)
    if not p.is_file():
        raise InputError(f"file not found: {data}")
    raw, header, rows = _read_table(p)
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        raise InputError(f"{data}: column(s) {missing} are needed and are not in the header "
                         f"{header}")
    grouped = "group" in header
    has_item = "item" in header
    has_cluster = has_item and "cluster" in header
    has_step = has_item and "reference_step" in header
    cases, undecided_items, rows_without_an_item = {}, set(), 0
    mixed_items, seen_ids, duplicate_ids = set(), set(), 0

    def fresh():
        return {k: 0 for k in _COUNTS}

    total, by_group, disagreements, undecided = fresh(), {}, [], []
    methods = {"exact": 0, "float": 0}
    blank = 0
    for line, cells in rows:
        if not cells:
            blank += 1
            continue
        group = None
        if len(cells) == len(header):
            row = dict(zip(header, cells))
            group = row["group"].strip() if grouped else None
        tallies = [total] + ([by_group.setdefault(group, fresh())] if grouped and group is not None
                             else [])
        for t in tallies:
            t["rows"] += 1
        if len(cells) != len(header):
            total["undecided"] += 1
            undecided.append({"line": line, "id": None, "group": None, "reason": "row_length",
                              "detail": f"{len(cells)} cells, header has {len(header)}"})
            continue
        ident = row["id"]
        if ident in seen_ids:
            duplicate_ids += 1
        seen_ids.add(ident)
        engine, verdict, r, method = _decide(row)
        if engine is None:
            for t in tallies:
                t["undecided"] += 1
            detail = r.label if r is not None else ""
            if verdict == "at_the_edge":
                detail = ("the value is within floating-point noise of the edge of the tolerance "
                          "after unit conversion; write both in one unit to decide it exactly")
            undecided.append({"line": line, "id": ident, "group": group, "reason": verdict,
                              "detail": detail})
            if has_item and row["item"].strip():
                undecided_items.add((group, row["item"].strip()))
            continue
        grader = _read_verdict(row["grader_verdict"])
        if grader is None:
            for t in tallies:
                t["grader_unreadable"] += 1
            undecided.append({"line": line, "id": ident, "group": group,
                              "reason": "grader_verdict_unreadable",
                              "detail": row["grader_verdict"]})
            if has_item and row["item"].strip():
                undecided_items.add((group, row["item"].strip()))
            continue
        for t in tallies:
            t["decided"] += 1
        methods[method] += 1
        outcome = "right" if grader == engine else ("lenient" if grader == "met" else "strict")
        if has_item and not row["item"].strip():
            rows_without_an_item += 1           # counted as a row, not as an item
        elif has_item:
            case = cases.setdefault((group, row["item"].strip()), {
                "outcomes": [], "clusters": [], "rounding": None})
            case["outcomes"].append(outcome)
            if has_cluster and row["cluster"].strip() and row["cluster"].strip() not in case["clusters"]:
                case["clusters"].append(row["cluster"].strip())
            ref_key = (row["reference_value"].strip(), row["reference_unit"].strip(), row["tolerance"].strip())
            if case.setdefault("reference", ref_key) != ref_key:
                mixed_items.add((group, row["item"].strip()))
            if outcome == "lenient" and has_step:
                r3 = _rounding(row)
                if r3 is not None:              # several lenient rows: outside if any of them is
                    old = case["rounding"] or (False, False, False)
                    case["rounding"] = tuple(a or b for a, b in zip(old, r3))
        if grader == engine:
            for t in tallies:
                t["right"] += 1
            continue
        kind = outcome
        for t in tallies:
            t[kind] += 1
        disagreements.append({
            "line": line, "id": ident, "group": group, "kind": kind,
            "grader_verdict": grader, "engine_verdict": verdict,
            "reference": f"{row['reference_value'].strip()} {row['reference_unit'].strip()}",
            "stated": f"{row['stated_value'].strip()} {row['stated_unit'].strip()}",
            "tolerance": row["tolerance"].strip(),
            "difference": r.difference, "difference_unit": r.unit, "method": method,
            "row_sha256": sha256_json(row),
        })

    summary = dict(total, blank_lines=blank, decided_exact=methods["exact"],
                   decided_float=methods["float"])
    if duplicate_ids:
        summary["rows_with_a_repeated_id"] = duplicate_ids
    if grouped:
        summary["by_group"] = {g: by_group[g] for g in sorted(by_group)}
    if has_item:
        summary["by_item"] = _by_item(cases, has_cluster, has_step)
        summary["rows_without_an_item"] = rows_without_an_item
        summary["items_with_no_decided_row"] = len(undecided_items - set(cases))
        summary["items_with_more_than_one_reference"] = len(mixed_items)
    result = {"summary": summary, "disagreements": disagreements, "undecided": undecided,
              "header": header}
    out = GraderResult(summary=summary, disagreements=disagreements, undecided=undecided,
                       receipt={})
    result["exit_code"] = out.exit_code
    receipt = {
        "receipt": GRADER_RECEIPT_SCHEMA,
        "command": "grader-check",
        "consilience_version": ENGINE_VERSION,       # the engine that read the units
        "judge_check_version": __version__,          # this package
        "pint_version": PINT_VERSION,
        "inputs": {"data": {"path": str(data), "sha256": sha256_bytes(raw), "bytes": len(raw)}},
        "options": {"precision": "exact", "edge_guard": EDGE_GUARD,
                    "met_words": sorted(MET_WORDS), "unmet_words": sorted(UNMET_WORDS)},
        "result": result,
    }
    receipt["sha256"] = sha256_json(receipt)
    out.receipt = receipt
    return out


def _restamp(fresh: dict, recorded: dict) -> str:
    """Hash of a fresh receipt stamped with the versions the recorded one names, so that
    the hash compares inputs and result only. Receipts written before this package had
    its own version number carry no ``judge_check_version``; for them, and only for
    that field, the fresh receipt's value is left out."""
    r = {k: v for k, v in fresh.items() if k != "sha256"}
    for key in ("consilience_version", "pint_version", "judge_check_version"):
        if key in recorded:
            r[key] = recorded[key]
    if "judge_check_version" not in recorded:
        r.pop("judge_check_version", None)
    return sha256_json(r)


def _table_of(stored: str, override, receipt_path: Optional[Path]) -> Path:
    """Where the table of a receipt is now: where ``--data`` says, else the recorded path
    (from the working directory, then from the receipt's folder), else a file of the
    same name beside the receipt. Whichever is found is then checked by hash."""
    from consilience.verify import _resolve
    try:
        return _resolve(stored, override, receipt_path)
    except InputError:
        if override is None and receipt_path is not None:
            beside = Path(receipt_path).resolve().parent / Path(stored).name
            if beside.is_file():
                return beside
        raise


def verify_grader(rec: dict, *, data_path=None, receipt_path: Optional[Path] = None):
    """Re-run a grader receipt. Returns (ok, steps, recomputed_sha256)."""
    recorded = rec.get("sha256")
    steps = []
    integrity = sha256_json({k: v for k, v in rec.items() if k != "sha256"})
    steps.append(("receipt hash", integrity == recorded,
                  "matches its contents" if integrity == recorded else
                  f"recorded {recorded}, contents hash to {integrity}: the receipt was edited"))
    try:
        stored = rec["inputs"]["data"]
        p = _table_of(stored["path"], data_path, receipt_path)
    except (KeyError, TypeError) as exc:
        raise InputError(f"the receipt is missing a field: {exc}") from None
    got = sha256_bytes(p.read_bytes())
    dok = got == stored["sha256"]
    steps.append(("data hash", dok, f"{p} " + ("matches" if dok else
                                                f"hashes to {got}, recorded {stored['sha256']}: "
                                                "the data changed")))
    recomputed = None
    if dok:
        fresh = check_grader(p).receipt
        fresh["inputs"]["data"]["path"] = stored["path"]   # where it was, as recorded
        recomputed = _restamp(fresh, rec)
        same = recomputed == recorded == integrity
        steps.append(("re-run", same, "same result" if same else
                      "the re-run gives a different result from the receipt"))
    else:
        steps.append(("re-run", False, "not re-run (see above)"))
    return all(s[1] for s in steps), steps, recomputed


__all__ = ["GRADER_RECEIPT_SCHEMA", "GraderResult", "check_grader", "verify_grader"]
