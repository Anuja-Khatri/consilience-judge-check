"""consilience-judge-check: where a rubric's right answer is arithmetic, is the judge right?

    from consilience_judge_check import scan_rubric, build_probes, probe_table, check_grader

    s = scan_rubric("rubric.csv")                       # criteria that arithmetic can check
    rows, skipped, csv_text = build_probes(s.receipt)   # responses with a known right verdict
    # ... grade the probes with your own judge and write verdicts.csv ...
    table_text, summary = probe_table("probes.csv", "verdicts.csv")
    g = check_grader("table.csv")                       # the judge's verdicts against arithmetic
    g.summary, g.disagreements, g.undecided

No judge and no model is run by this package. Units are read by the Consilience engine
(the ``consilience`` package); every row in one unit is decided in exact decimal
arithmetic.
"""
from ._version import __version__
from .units import CURRENCY_UNITS, register_currencies  # teaches the engine the currency codes
from .grader import GRADER_RECEIPT_SCHEMA, GraderResult, check_grader
from .rubric import (CONTRACTS_SCHEMA, PROBES_SCHEMA, ScanResult, build_probes, probe_table,
                     read_criterion, scan_rubric)
from .verify import VerifyResult, verify

__all__ = ["__version__", "scan_rubric", "build_probes", "probe_table", "check_grader", "verify",
           "read_criterion", "ScanResult", "GraderResult", "VerifyResult", "CONTRACTS_SCHEMA",
           "PROBES_SCHEMA", "GRADER_RECEIPT_SCHEMA", "CURRENCY_UNITS", "register_currencies"]
