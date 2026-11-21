"""``verify``: re-run a receipt written by this package and confirm its hash.

Three kinds of file are receipts here: the contracts file ``scan`` writes, the receipt
``probes`` writes, and the report ``check`` writes. Each names its inputs by hash.
``verify`` reads the inputs again, repeats the work, and says whether the result is the
same. It means "re-runs to the same answer". It does not say who wrote the receipt.

A receipt written by the Consilience engine itself (``consilience compare``, ``check``
or ``compare-table``) is handed to the engine's own ``verify``, so that one command
re-runs every receipt a study folder holds.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from consilience.compare import InputError
from consilience.units import rules_of

from .grader import GRADER_RECEIPT_SCHEMA, verify_grader
from .rubric import CONTRACTS_SCHEMA, PROBES_SCHEMA, verify_probes, verify_scan

EXIT_OK, EXIT_FAILED = 0, 1


@dataclass
class VerifyResult:
    ok: bool
    command: str
    recorded_sha256: Optional[str]
    recomputed_sha256: Optional[str]
    steps: list = field(default_factory=list)       # (name, ok, detail)

    @property
    def exit_code(self) -> int:
        return EXIT_OK if self.ok else EXIT_FAILED


def verify(receipt: Union[str, Path, dict], *, data=None) -> VerifyResult:
    """Re-run the result recorded in ``receipt`` (a path or a dict) and confirm its hash.

    ``data`` says where the input file is now, if it has moved: the rubric of a contracts
    file, the contracts file of a probes receipt, the table of a ``check`` receipt.
    Raises ``InputError`` if the file is not a receipt of this package or cannot be used.
    """
    rpath = None
    if isinstance(receipt, (str, Path)):
        rpath = Path(receipt)
        if not rpath.is_file():
            raise InputError(f"file not found: {receipt}")
        try:
            rec = json.loads(rpath.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise InputError(f"{receipt}: not JSON: {exc}") from None
    else:
        rec = receipt
    if not isinstance(rec, dict):
        raise InputError("a receipt must be a JSON object")
    kind = rec.get("receipt")
    try:
        with rules_of(rec.get("consilience_version")):
            if kind in (CONTRACTS_SCHEMA, PROBES_SCHEMA):
                scan = kind == CONTRACTS_SCHEMA
                ok, steps, recomputed = (verify_scan if scan else verify_probes)(rec, data, rpath)
                command = "scan" if scan else "probes"
            elif kind == GRADER_RECEIPT_SCHEMA:
                ok, steps, recomputed = verify_grader(rec, data_path=data, receipt_path=rpath)
                command = "check"
            else:
                kind = None
    except (KeyError, TypeError, AttributeError) as exc:
        raise InputError(f"the receipt is damaged: {type(exc).__name__}: {exc}") from None
    if kind is None:                      # not ours: perhaps the engine's own
        from consilience.verify import verify as engine_verify
        try:
            v = engine_verify(rpath if rpath is not None else rec, data=data)
        except InputError as exc:
            raise InputError(
                "not a receipt this package or the Consilience engine can re-run (this "
                f"package writes \"{CONTRACTS_SCHEMA}\", \"{PROBES_SCHEMA}\" and "
                f"\"{GRADER_RECEIPT_SCHEMA}\"); the engine says: {exc}") from None
        return VerifyResult(ok=v.ok, command=f"consilience {v.command}",
                            recorded_sha256=v.recorded_sha256,
                            recomputed_sha256=v.recomputed_sha256, steps=list(v.steps))
    return VerifyResult(ok=ok, command=command, recorded_sha256=rec.get("sha256"),
                        recomputed_sha256=recomputed, steps=steps)


__all__ = ["VerifyResult", "verify"]
