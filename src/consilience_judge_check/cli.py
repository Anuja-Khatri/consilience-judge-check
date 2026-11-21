"""The ``consilience-judge-check`` command.

    consilience-judge-check scan rubric.csv --out contracts.json --review review.csv
    consilience-judge-check probes contracts.json --out probes.csv --receipt probes_receipt.json
    consilience-judge-check table probes.csv verdicts.csv --out table.csv
    consilience-judge-check check table.csv --receipt receipt.json
    consilience-judge-check verify receipt.json

Exit codes. ``check``: 0 the grader agrees with the arithmetic on every row, 1 it differs
on some rows, 3 some rows could not be decided. ``verify``: 0 the receipt re-runs to the
same result, 1 it does not. Every command: 64 for an input that cannot be used, and 2
for a command line that cannot be read (a missing or unknown option).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from consilience.compare import InputError

from ._version import __version__

PROG = "consilience-judge-check"
EXIT_USAGE = 64
EXIT_BROKEN_PIPE = 141


def _g(x) -> str:
    return f"{x:.6g}" if isinstance(x, float) else str(x)


def _write_receipt(path, receipt) -> None:
    Path(path).write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def _error(message) -> int:
    print(f"{PROG}: error: {message}", file=sys.stderr)
    return EXIT_USAGE


# -------------------------------------------------------------------- check
def _fmt_grader(g, data) -> str:
    rec, s = g.receipt, g.summary
    out = [f"data:        {data} ({s['rows']} rows; sha256 {rec['inputs']['data']['sha256']})",
           f"decided:     {s['decided']} of {s['rows']} ({s['decided_exact']} in exact decimal "
           f"arithmetic, {s['decided_float']} after a unit conversion)",
           f"grader right: {s['right']}",
           f"lenient:     {s['lenient']} (accepted a value outside the stated tolerance)",
           f"strict:      {s['strict']} (rejected a value inside the stated tolerance)"]
    for d in g.disagreements:
        grp = f"{d['group']}  " if d["group"] else ""
        diff = (f", difference {_g(d['difference'])} {d['difference_unit']}"
                if d["difference"] is not None else "")
        out.append(f"  line {d['line']:<4} {d['id']}  {grp}{d['kind']}: stated {d['stated']}, "
                   f"reference {d['reference']}, tolerance {d['tolerance']}{diff}   "
                   f"row receipt {d['row_sha256'][:12]}")
    for name, counts in (s.get("by_group") or {}).items():
        out.append(f"  group {name}: {counts['right']} right, {counts['lenient']} lenient, "
                   f"{counts['strict']} strict of {counts['decided']} decided")
    if s.get("by_item"):
        out.append("by item (an item is wrong if any of its rows is; 95% interval treats items "
                   "as independent):")
        for name, e in s["by_item"].items():
            lo, hi = e["wrong_share_95"] or (0.0, 0.0)
            line = (f"  {name or '(all)'}: {e['wrong_at_least_once']} of {e['items']} items wrong "
                    f"({100 * lo:.0f}% to {100 * hi:.0f}%), {e['wrong_on_every_row']} on every row")
            if "clusters" in e:
                line += (f"; in {e['clusters_with_a_wrong_item']} of {e['clusters']} clusters "
                         f"(largest cluster {e['largest_cluster']['wrong']} of "
                         f"{e['largest_cluster']['items']}, the others "
                         f"{e['other_clusters']['wrong']} of {e['other_clusters']['items']})")
            if e.get("largest_cluster_is_tied"):
                line += " (several clusters are the largest; the first by name is shown)"
            if "lenient_items_rounding_checked" in e and e["lenient_at_least_once"]:
                line += (f"; of {e['lenient_at_least_once']} accepted, "
                         f"{e['lenient_items_still_outside_after_rounding_half_up']} still outside "
                         f"after rounding to the reference's precision, "
                         f"{e['lenient_items_still_outside_after_rounding_toward_reference']} even "
                         f"when rounded toward the reference")
                if e["lenient_items_rounding_not_checked"]:
                    line += f" ({e['lenient_items_rounding_not_checked']} could not be checked)"
            out.append(line)
        if s.get("rows_without_an_item"):
            out.append(f"  {s['rows_without_an_item']} rows name no item and are counted as rows only")
        if s.get("items_with_no_decided_row"):
            out.append(f"  {s['items_with_no_decided_row']} items have no decided row and are not counted")
        if s.get("items_with_more_than_one_reference"):
            out.append(f"  {s['items_with_more_than_one_reference']} items have rows with different "
                       f"references or tolerances: one label is being used for more than one case")
        for name, e in s["by_item"].items():
            if e.get("items_in_more_than_one_cluster") or e.get("items_without_a_cluster"):
                out.append(f"  {name or '(all)'}: {e.get('items_in_more_than_one_cluster', 0)} items are "
                           f"named in more than one cluster (counted in the first), "
                           f"{e.get('items_without_a_cluster', 0)} name no cluster")
    if s.get("rows_with_a_repeated_id"):
        out.append(f"  {s['rows_with_a_repeated_id']} rows repeat an id already used; each is counted")
    n = s["undecided"] + s["grader_unreadable"]
    out.append(f"could not decide: {n} row{'s' if n != 1 else ''}"
               + (" (not counted; nothing was guessed)" if n else ""))
    for u in g.undecided:
        out.append(f"  line {u['line']:<4} {u['id']}  {u['reason']}"
                   + (f": {u['detail']}" if u["detail"] else ""))
    meaning = {0: ("the grader agrees with the arithmetic on every row" if s["rows"] else
                   "the table has no rows: nothing was checked"),
               1: "the grader differs from the arithmetic on some rows",
               3: "some rows could not be decided, so the check is incomplete"}
    out.append(f"result:      exit {g.exit_code}: {meaning[g.exit_code]}")
    out.append(f"receipt:     sha256 {rec['sha256']}")
    return "\n".join(out)


def cmd_check(args) -> int:
    from .grader import check_grader
    try:
        g = check_grader(args.data)
    except InputError as exc:
        return _error(exc)
    if args.receipt:
        try:
            _write_receipt(args.receipt, g.receipt)
        except OSError as exc:
            return _error(f"cannot write {args.receipt}: {exc}")
    if args.json:
        print(json.dumps(g.receipt, indent=2, ensure_ascii=False))
    else:
        print(_fmt_grader(g, args.data))
        if args.receipt:
            print(f"wrote:       {args.receipt}")
    return g.exit_code


# --------------------------------------------------------------------- scan
def _fmt_scan(r, path) -> str:
    c, rec = r.counts, r.receipt
    pct = (lambda a, b: f"{100 * a / b:.1f}%" if b else "n/a")
    out = [f"rubric:             {path} ({c['criteria']} criteria; sha256 "
           f"{rec['inputs']['rubric']['sha256']})",
           f"contain 'within +/-' or the plus-minus sign: {c['contain_within_plus_or_minus']} "
           f"({pct(c['contain_within_plus_or_minus'], c['criteria'])})"
           + (f", in {c['groups_containing_within_plus_or_minus']} of {c['groups']} groups"
              if "groups" in c else ""),
           f"checkable by rule:  {c['checkable']}"
           + (f", in {c['groups_with_a_checkable_criterion']} groups" if "groups" in c else "")]
    if c.get("percent_tolerance_read_as_points"):
        out.append(f"  of those, {c['percent_tolerance_read_as_points']} give a percent tolerance on a "
                   f"percentage; it is read as percentage points")
    left = sum(c["left_out"].values())
    out.append(f"left out:           {left} not read"
               + (" (counted by reason; nothing was guessed)" if left else ""))
    for reason, n in c["left_out"].items():
        out.append(f"  {n:>5}  {reason}")
    w = c.get("weight")
    if w and w["checkable_share"] is not None:
        line = (f"weight:             the checkable criteria carry {w['checkable']} of "
                f"{w['positive_total']} positive weight ({100 * w['checkable_share']:.1f}%)")
        if "share_within_a_group_min" in w:
            line += (f"; in the {w['groups_with_a_share']} groups that have one, from "
                     f"{100 * w['share_within_a_group_min']:.1f}% to "
                     f"{100 * w['share_within_a_group_max']:.1f}% of the group's weight")
        out.append(line)
    out.append(f"contracts:          sha256 {rec['sha256']}")
    return "\n".join(out)


def cmd_scan(args) -> int:
    from .rubric import DEFAULT_LEAD, scan_rubric
    try:
        r = scan_rubric(args.rubric, lead=args.lead or DEFAULT_LEAD, where=args.where)
    except InputError as exc:
        return _error(exc)
    if args.out:
        try:
            _write_receipt(args.out, r.receipt)
        except OSError as exc:
            return _error(f"cannot write {args.out}: {exc}")
    if args.review:
        import csv as _csv
        try:
            with open(args.review, "w", newline="", encoding="utf-8") as f:
                w = _csv.writer(f, lineterminator="\n")
                w.writerow(["id", "criterion", "value_read", "tolerance_read", "unit_read", "note"])
                for i in r.items:
                    w.writerow([i["id"], i["criterion"], i["value"], i["tolerance"], i["unit"],
                                "percent tolerance read as percentage points"
                                if i.get("percent_tolerance_read_as_points") else ""])
        except OSError as exc:
            return _error(f"cannot write {args.review}: {exc}")
    if args.json:
        print(json.dumps(r.receipt, indent=2, ensure_ascii=False))
    else:
        print(_fmt_scan(r, args.rubric))
        if args.out:
            print(f"wrote:              {args.out}")
        if args.review:
            print(f"to review:          {args.review} (read it: the reader is careful, not proven)")
        elif r.items:
            print("to review:          run again with --review FILE and read what was accepted")
    return 0


# ------------------------------------------------------------------- probes
def cmd_probes(args) -> int:
    from .rubric import DEFAULT_OFFSETS, build_probes, probes_receipt
    try:
        if args.offsets is None:
            offsets = list(DEFAULT_OFFSETS)
        else:
            offsets = [o.strip() for o in args.offsets.split(",") if o.strip()]
            if not offsets:
                raise InputError("--offsets is empty")
        if not Path(args.contracts).is_file():
            raise InputError(f"file not found: {args.contracts}")
        try:
            contracts = json.loads(Path(args.contracts).read_text(encoding="utf-8"))
        except ValueError as exc:
            raise InputError(f"{args.contracts}: not JSON: {exc}") from None
        rows, skipped, text = build_probes(contracts, offsets)
        Path(args.out).write_bytes(text.encode("utf-8"))
        rec = probes_receipt(args.contracts, contracts, offsets, rows, skipped, text, args.out)
        if args.receipt:
            _write_receipt(args.receipt, rec)
    except (InputError, OSError) as exc:
        return _error(exc)
    print(f"contracts:   {args.contracts} ({len(contracts['result']['items'])} checkable criteria)")
    print(f"offsets:     {', '.join(offsets)} (in tolerances from the reference)")
    print(f"probes:      {len(rows)}, the right verdict of each fixed by arithmetic")
    for reason, n in skipped.items():
        print(f"  not written: {n}  {reason}")
    print(f"wrote:       {args.out} (sha256 {rec['result']['output']['sha256']})")
    if args.receipt:
        print(f"receipt:     {args.receipt}")
    return 0


# -------------------------------------------------------------------- table
def cmd_table(args) -> int:
    from .rubric import probe_table
    try:
        text, summary = probe_table(args.probes, args.verdicts)
        Path(args.out).write_bytes(text.encode("utf-8"))
    except (InputError, OSError) as exc:
        return _error(exc)
    print(f"rows:        {summary['rows']} graded cases, on {summary['probes_graded']} of "
          f"{summary['probes']} probes")
    if summary["probes_without_a_verdict"]:
        print(f"  {summary['probes_without_a_verdict']} probes have no verdict and are not in the table")
    print(f"wrote:       {args.out}")
    print(f"next:        {PROG} check {args.out} --receipt receipt.json")
    return 0


# ------------------------------------------------------------------- verify
def cmd_verify(args) -> int:
    from .verify import verify
    try:
        v = verify(args.receipt, data=args.data)
    except InputError as exc:
        return _error(exc)
    print(f"{'ok' if v.ok else 'FAILED'}: {args.receipt} ({v.command})")
    for name, ok, detail in v.steps:
        print(f"  {'ok ' if ok else 'BAD'} {name}: {detail}")
    if v.recorded_sha256:
        print(f"  recorded sha256   {v.recorded_sha256}")
    if v.recomputed_sha256 and v.recomputed_sha256 != v.recorded_sha256:
        print(f"  recomputed sha256 {v.recomputed_sha256}")
    return v.exit_code


# ------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Find the criteria of a rubric whose right verdict is arithmetic, build a "
                    "test for a grader from them, and report where the grader is wrong. No "
                    "grader and no model is run.")
    ap.add_argument("--version", action="version", version=f"{PROG} {__version__}")
    sub = ap.add_subparsers(dest="command", metavar="{scan,probes,table,check,verify}")

    rs = sub.add_parser("scan", help="find the criteria that state one value and a tolerance")
    rs.add_argument("rubric", help="the rubric (CSV with columns id and criterion; optional "
                                   "weight and group)")
    rs.add_argument("--lead", action="append", metavar="WORD",
                    help="a word a criterion must start with (default: States); repeatable")
    rs.add_argument("--where", action="append", metavar="COLUMN=VALUE",
                    help="use only rows where the column holds the value; repeatable")
    rs.add_argument("--out", metavar="FILE", help="write the contracts file (JSON) to FILE")
    rs.add_argument("--review", metavar="FILE",
                    help="write a table (CSV) of every accepted criterion and how it was read, "
                         "for a person to check")
    rs.add_argument("--json", action="store_true", help="print the contracts file as JSON")
    rs.set_defaults(func=cmd_scan)

    rp = sub.add_parser("probes", help="write responses whose right verdict is fixed by "
                                       "arithmetic")
    rp.add_argument("contracts", help="the contracts file written by `scan --out`")
    rp.add_argument("--offsets", metavar="LIST",
                    help="distances from the reference in tolerances, comma-separated "
                         "(default: 0,+0.5,+0.9,+1.1,+2,-0.5,-0.9,-1.1,-2,far); a trailing u "
                         "writes a dollar amount in another unit (+1.1u)")
    rp.add_argument("--out", metavar="FILE", required=True, help="write the probes (CSV) to FILE")
    rp.add_argument("--receipt", metavar="FILE", help="also write a receipt to FILE")
    rp.set_defaults(func=cmd_probes)

    rt = sub.add_parser("table", help="join a grader's verdicts on the probes into the table "
                                      "`check` reads")
    rt.add_argument("probes", help="the probes file written by `probes`")
    rt.add_argument("verdicts", help="the grader's verdicts (CSV with probe_id and verdict; "
                                     "optional call and context)")
    rt.add_argument("--out", metavar="FILE", required=True, help="write the table (CSV) to FILE")
    rt.set_defaults(func=cmd_table)

    g = sub.add_parser("check",
                       help="check a grader's verdicts where the right answer is arithmetic "
                            "(exit 0/1/3, 64 error)")
    g.add_argument("data", help="the table of graded cases (CSV with a header row)")
    g.add_argument("--json", action="store_true", help="print the full report as JSON")
    g.add_argument("--receipt", metavar="FILE", help="also write the JSON report to FILE")
    g.set_defaults(func=cmd_check)

    v = sub.add_parser("verify", help="re-run a receipt and confirm its hash (exit 0/1, 64 error)")
    v.add_argument("receipt", help="a contracts file, a probes receipt or a check receipt; a "
                                    "receipt of the Consilience engine is handed to the engine")
    v.add_argument("--data", help="where the receipt's input file is now, if it has moved")
    v.set_defaults(func=cmd_verify)
    return ap


def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_help(sys.stderr)
        return EXIT_USAGE
    try:
        return args.func(args)
    except BrokenPipeError:
        # The reader closed the pipe early (`| head -1`). Exit quietly, as command-line
        # tools do, instead of printing a traceback.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return EXIT_BROKEN_PIPE


if __name__ == "__main__":
    sys.exit(main())
