"""``rubric``: find the part of a rubric that arithmetic can check, and build the test.

A rubric is a list of criteria a grader marks MET or UNMET. Most need judgement. Some
state one value and a tolerance, for example

    States Q3 revenue as $30.8B (within +/- $0.5B)

and for those the right verdict is a comparison of two numbers. This module does three
things with such criteria. None of them runs a grader or a model.

``scan``    read a rubric (a CSV file, one criterion per row) and find the criteria that
            state exactly one value and a tolerance. Count them, say how much of the
            weight they carry, and count every other criterion under the reason it was
            left out. The result is a contracts file with a receipt.
``probes``  for each such criterion, write short responses that state a value at a known
            distance from the reference: on it, inside the tolerance, just inside, just
            outside, outside, far off. The right verdict of each is fixed by arithmetic.
``table``   join the verdicts a grader gave on those probes into the table that
            ``check`` reads.

Then ``consilience-judge-check check`` decides every row and reports where the grader
was lenient or strict.

What is read, and what is not (version 1). The reader is an allow-list: a criterion is
used only if it matches a narrow pattern in full, and is otherwise left out and counted
under a reason. A criterion is used only if

* it is plain ASCII text of at most 600 characters, starts with a lead word (default
  ``States``) and ends with ``(within +/- T)``;
* every word in it that holds a digit is recognised in full, as a date or period label
  (a year, Q3, FY25, H1, 9/30/2025, 5-year, a day after a month name) or as the value;
* the value comes straight after one of a few words ("as", "was", "is", "of", "issued",
  "provided", "suffered"). A number anywhere else is not guessed at;
* the value is a dollar amount (``$``, with k, thousand, M, million, B, billion), a
  percentage (``%``, pp, ppts, bps) or a count, with or without a word ("705,593
  shares", "3.24x"), positive, with regular thousands commas and at most 20 digits;
* the tolerance is the same kind of thing as the value, is read in full, carries a scale
  if the value does, and is smaller than the value;
* it has no wording this version does not read: hedges, one-sided or negated statements,
  alternatives and comparisons, a second clause joined by "and", brackets, rates, signs
  in words, other currencies, numbers written as words.

Leaving a criterion out is always safe: it only means that criterion is not tested.

Two readings are choices. A tolerance written with a percent sign on a percentage
("5.31% (within +/- 0.1%)") is read as percentage points, and the item carries
``percent_tolerance_read_as_points``. A stated decline or loss ("suffered $40,000 loss")
is read as its size; the probe sentence keeps the wording.

**The reader is careful, not proven.** Three independent audits each wrote hostile
criteria to break it, and each found ones it misread; it was rewritten after each. It
has met one real rubric. ``scan --review`` writes every accepted criterion with
the value and tolerance read from it: check that list before trusting probes built from it.

Arithmetic is exact decimal arithmetic on the digits as written, carried to 100 digits.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Optional, Sequence, Union

from consilience import __version__ as ENGINE_VERSION
from consilience.check import _read_table
from consilience.compare import InputError
from consilience.hashing import sha256_bytes, sha256_json

from ._version import __version__

CONTRACTS_SCHEMA = "consilience-rubric-contracts/v1"
PROBES_SCHEMA = "consilience-rubric-probes/v1"
DEFAULT_LEAD = ("States",)
DEFAULT_OFFSETS = ("0", "+0.5", "+0.9", "+1.1", "+2", "-0.5", "-0.9", "-1.1", "-2", "far")
PROBE_COLUMNS = ("probe_id", "item", "cluster", "criterion", "response", "offset",
                 "stated_value", "stated_unit", "reference_value", "reference_unit",
                 "tolerance", "reference_step", "right_verdict")
# The first line of a probes file and of a table is a comment that names the command that
# wrote it. Files written while these commands were part of the ``consilience`` package
# name them as they were called there. ``verify`` accepts both, so that those files
# still verify byte for byte.
PROBES_COMMENT = ("# Probes built by `consilience-judge-check probes`. The right verdict of each is "
                  "fixed by arithmetic.\n")
PROBES_COMMENT_AS_FIRST_WRITTEN = ("# Probes built by `consilience rubric probes`. The right verdict "
                                   "of each is fixed by arithmetic.\n")
TABLE_COMMENT = ("# One row per graded probe, built by `consilience-judge-check table`. The right "
                 "verdict is not here: `check` works it out from the numbers. `group` is the probe's "
                 "distance, kept for counting.\n")
TABLE_COMMENT_AS_FIRST_WRITTEN = ("# One row per graded probe, built by `consilience rubric table`. "
                                  "The right verdict is not here: grader-check works it out from the "
                                  "numbers. `group` is the probe's distance, kept for counting.\n")
TABLE_COLUMNS = ("id", "reference_value", "reference_unit", "tolerance", "stated_value",
                 "stated_unit", "grader_verdict", "group", "item", "cluster", "reference_step")

# ------------------------------------------------------------------ reading a criterion
#
# An allow-list. The criterion is cut into words. Every word that holds a digit must be
# recognised in full, as a date or period label or as the one value; anything else and
# the criterion is left out. Only plain ASCII text is read. This design replaced a
# block-list after two independent audits each found inputs the block-list misread.

_SCALE = {"k": 10 ** 3, "thousand": 10 ** 3, "m": 10 ** 6, "mm": 10 ** 6, "mn": 10 ** 6,
          "million": 10 ** 6, "b": 10 ** 9, "bn": 10 ** 9, "billion": 10 ** 9}
_SCALE = {k: Decimal(v) for k, v in _SCALE.items()}
_SCALE_WORDS = ("thousand", "million", "billion")      # the only scales read without a "$"
_PCT_SCALE = {"%": Decimal(1), "pp": Decimal(1), "ppt": Decimal(1), "ppts": Decimal(1),
              "percentage points": Decimal(1), "bps": Decimal("0.01")}
_UNIT_OF = {"money": "USD", "percent": "percent", "count": "count"}
_MAX_DIGITS = 20                                        # longer numbers are not read
_MAX_LENGTH = 600                                       # longer criteria are not read
_PRECISION = 100                                        # digits kept in every calculation

_MENTIONS_PLUS_OR_MINUS = re.compile(r"within\s*\+/-|±")
_TOLERANCE = re.compile(r" ?\( ?within ?\+/- ?(?P<tol>[^()]{1,40}?) ?\)$")
_NUM = r"\d[\d,]*(?:\.\d+)?"
_GROUPED = re.compile(r"[1-9]\d{0,2}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september",
           "october", "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
           "sep", "sept", "oct", "nov", "dec")
# The value must come straight after one of these words ("revenue as $5M", "issued 4,561,714
# shares"). A number anywhere else in the claim is not guessed at: the criterion is left out.
_ANCHORS = ("as", "was", "is", "of", "issued", "provided", "suffered")
# a word that holds a digit and is a date or period label, in full
_DATE_WORD = re.compile(r"(?:19|20)\d{2}|Q[1-4]|FY\d{2,4}|H[12]|\d{1,2}/\d{1,2}/\d{2,4}|"
                        r"\d{1,2}-(?:year|month|day|week)")
_YEAR = re.compile(r"(?:19|20)\d{2}")
# a word that is the value, in full: sign, dollar sign, number, and a unit written against it
_VALUE_WORD = re.compile(rf"(?P<sign>\+)?(?P<cur>\$)?(?P<num>{_NUM})"
                         rf"(?P<unit>%|pp|ppts|ppt|bps|K|k|M|m|mm|B|bn)?(?P<x>x)?")
_UNIT_WORD = re.compile(r"%|pp|ppts|ppt|bps|thousand|million|billion|K|k|M|m|mm|B|bn")
# wording this version does not read: hedges, one-sided or negated statements, alternatives,
# comparisons, second clauses, brackets, rates, signs in words, other currencies, numbers as words
_NOT_READ = re.compile(
    r"\bor\b|approximately|approx\.?|about|around|roughly|nearly|almost|circa|\bca?\.|close to|"
    r"\bsome\b|estimated|~|\bvs\.?\b|versus|\bfrom\b|\bbetween\b|\bboth\b|\busing\b|"
    r"at least|at most|more than|less than|fewer than|greater than|in excess of|over\b|under\b|"
    r"above|below|exceed\w*|surpass\w*|topped|capped|up to|upwards? of|north of|south of|shy of|"
    r"higher than|lower than|region of|order of|as (?:high|low|many|much|few|little) as|nearest|"
    r"\bless\b|\bmax\b|\bmin\b|\bno\b|in the red|\bCR\b|\bDR\b|\bupto\b|at-least|at-most|"
    r"larger than|smaller than|short of|nearing|\bplus\b|\bodd\b|\best\b|\babt\b|\bca\b|"
    r"\b(?:thousands|millions|billions|trillions)\b|\$(?:k|m|mm|bn|b)\b|"
    r"\b(?:am|pm|hours|hrs|o'clock|version|release|subzero|degrees)\b|"
    r"\b(?:quarter|third|fifth|tenth|fraction|multiple|share|portion) of\b|\bpct\b|\bbps?\b(?=.*\bbitrate\b)|"
    r"\bnot\b|n't\b|\bnever\b|cannot|range|minimum|maximum|[<>]|\be\.g\.|such as|similar|"
    r"\band\b|;|\(|\)|/(?!\d)|\bper\b|\bpercent\b|per cent|\beach\b|apiece|"
    r"\ba (?:user|share|seat|head|person|unit|month|year|day|week)\b|"
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|dozen|half|twice|double|triple)\b", re.I)
_NEGATIVE_WORD = re.compile(r"\bnegative\b|\bneg\b|\bminus\b|-ve\b", re.I)
# a magnitude word after the value that was not read as its unit
_SCALE_WORD_AFTER = re.compile(
    r"(?:thousands?|millions?|billions?|trillions?|tn|trn|mil|mill|mln|mio|mrd|bil|bln|bn|mn|mm|"
    r"hundreds?|lakhs?|lac|crores?|dozens?|quadrillions?|grand|mmm|k|m|b|t)\b\.?", re.I)
# another currency, named in words or by code or by country
_CURRENCY_WORD = re.compile(
    r"\b(?:dollars?|euros?|pounds?|sterling|yen|yuan|renminbi|rupees?|francs?|won|pesos?|"
    r"USD|EUR|GBP|JPY|INR|CNY|RMB|CAD|AUD|NZD|CHF|HKD|SGD|MXN|BRL|ZAR|KRW|SEK|NOK|DKK|"
    r"Rs\.?|rand|kr|bucks|quid|"
    r"US|Canadian|Australian|Singapore|Hong Kong|New Zealand|Mexican)\b", re.I)
_OTHER_UNITS = [("", Decimal(1)), (" thousand", Decimal(10) ** 3), (" million", Decimal(10) ** 6),
                (" billion", Decimal(10) ** 9)]


def _number(text: str) -> Optional[Decimal]:
    """Digits as written -> exact decimal. None unless the thousands commas are regular
    ("12,400", not "41,5", "0,385" or "1,00,000") and the number is not too long."""
    if not _GROUPED.fullmatch(text) or sum(c.isdigit() for c in text) > _MAX_DIGITS:
        return None
    return Decimal(text.replace(",", ""))


def _amount(text: str):
    """A tolerance such as '$0.5B', '15,000', '0.3 ppts', '$100k', '100 bps', '0.1x' -> dict,
    or None if any part of it is not understood."""
    text = text.replace("percentage points", "ppts").strip()
    m = re.fullmatch(rf"(?P<cur>\$)?(?P<num>{_NUM})(?P<gap> ?)(?P<unit>[A-Za-z%]{{1,12}})?"
                     rf"(?: (?P<noun>[A-Za-z]{{1,20}}))?", text)
    if not m:
        return None
    value = _number(m.group("num"))
    if value is None:
        return None
    currency = bool(m.group("cur"))
    unit, noun, gap = (m.group("unit") or ""), (m.group("noun") or ""), m.group("gap")
    low = unit.lower()
    kind, scale, scaled = ("money" if currency else "count"), Decimal(1), False
    if low in _PCT_SCALE:
        if currency:
            return None
        kind, scale = "percent", _PCT_SCALE[low]
    elif low in _SCALE:
        # without a "$", a letter may be a unit (5 K, 25 m, 10 M): only the spelled-out words
        # and a small k written against the number ("200k") are read as scales
        if not currency and low not in _SCALE_WORDS and not (unit == "k" and gap == ""):
            return None
        scale, scaled = _SCALE[low], True
    elif unit:
        if noun:
            return None                     # two words after the number
        unit, noun = "", unit               # '10 reams', '0.1x': a count with a word
    if noun and kind != "count":
        return None                         # '$5 mil', '5% relative': a word that is not understood
    return {"currency": currency, "kind": kind, "noun": noun, "value": value * scale,
            "scaled": scaled, "unit": low, "percent_sign": low == "%"}


def read_criterion(text: str, lead: Sequence[str] = DEFAULT_LEAD):
    """One criterion -> (item, None) if it states one value and a tolerance in a form this
    version recognises in full, else (None, reason). ``item`` holds the claim, the value
    and tolerance in base units as exact decimals, and how the number was written."""
    with localcontext() as ctx:
        ctx.prec = _PRECISION
        return _read(text, tuple(lead))


def _read(text: str, lead):
    if len(text) > _MAX_LENGTH:
        return None, "criterion_too_long"
    if not all(32 <= ord(c) < 127 for c in text):
        return None, "characters_not_read"          # only plain ASCII text is read
    head = next((w for w in lead if text.startswith(w + " ")), None)
    if head is None:
        return None, "does_not_start_with_a_lead_word"
    tm = _TOLERANCE.search(text)
    if not tm:
        return None, "no_trailing_tolerance"
    claim = text[len(head) + 1:tm.start()].strip()
    if claim.lower().startswith("that "):
        claim = claim[5:]
    if _NOT_READ.search(claim):
        return None, "wording_not_read"
    if _NEGATIVE_WORD.search(claim):
        return None, "negative_value"
    if _CURRENCY_WORD.search(claim):
        return None, "currency_not_read"
    tol = _amount(tm.group("tol"))
    if not tol or tol["value"] <= 0:
        return None, "tolerance_not_read"

    # every word that holds a digit must be a date or period label, or the one value
    words = [(m.start(), m.end(), m.group()) for m in re.finditer(r"\S+", claim)]
    values, has_year = [], False
    for i, (a, b, w) in enumerate(words):
        if not any(c.isdigit() for c in w):
            continue
        prev = words[i - 1][2] if i else ""
        anchored = prev.lower() in _ANCHORS
        if _DATE_WORD.fullmatch(w):
            if anchored and prev.lower() != "of":
                return None, "year_or_value_unclear"    # "headcount as 2024": a year or the value?
            has_year = has_year or bool(_YEAR.fullmatch(w)) or "-" in w
            continue
        if prev.lower().rstrip(".") in _MONTHS and re.fullmatch(r"\d{1,2},?", w):
            continue                                    # "June 30", "September 30,", "Sept 30"
        m = _VALUE_WORD.fullmatch(w)
        if m is None:
            if w.startswith(("-", "(")) or prev == "-":
                return None, "negative_value"
            if "$" in w and not w.startswith(("$", "+$")):
                return None, "currency_not_read"        # C$9.7M, HK$9.7M
            return None, "number_not_read"              # 2.5-year, 1H24, $3.2M-, 6.022e23, 30,800,
        if prev == "-" or prev.endswith("-"):
            return None, "negative_value"
        if m.group("cur") and re.fullmatch(r"[A-Z]{1,3}", prev):
            return None, "currency_not_read"            # A $5M, NZ $5M
        if not anchored:
            return None, "number_not_read"              # "the Top 1,000 customers", "Boeing 737"
        values.append((i, a, b, m))
    if len(values) != 1:
        return None, f"number_like_tokens_{len(values)}"
    i, a, b, m = values[0]
    currency, number = bool(m.group("cur")), m.group("num")
    unit_text = m.group("unit") or ""
    following = words[i + 1][2] if i + 1 < len(words) else ""
    if m.group("x"):
        if currency or unit_text:
            return None, "number_not_read"              # $3x, 5%x
        b -= 1                                          # "3.24x": the x stays in the sentence
    elif not unit_text and _UNIT_WORD.fullmatch(following):
        unit_text = " " + following                     # "$16,183 thousand", "5.5 %"
        b = words[i + 1][1]
        following = words[i + 2][2] if i + 2 < len(words) else ""
    unit = unit_text.strip().lower()
    value = _number(number)
    if value is None:
        return None, "number_not_read"                  # '41,5', '0,385', '1,00,000', too long
    if unit in _PCT_SCALE:
        if currency:
            return None, "number_not_read"              # $10%
        kind, scale = "percent", _PCT_SCALE[unit]
    else:
        kind, scale = ("money" if currency else "count"), _SCALE.get(unit, Decimal(1))
        if not currency and unit and unit not in _SCALE_WORDS:
            return None, "scale_letter_without_currency"    # 8,849 m, 373 K, 512 B: a unit?
    if _SCALE_WORD_AFTER.fullmatch(following) or re.match(r"[KkMmBbTt][^A-Za-z]", following) \
            or re.match(r"(?:thousand|million|billion|trillion|bn|mm|mn|lacs?|lakhs?|crores?)(?![a-z])",
                        following, re.I):
        return None, "scale_word_not_read"              # $2.5 trillion, $5 Million, $120 mln, $5 M&A
    if has_year and not (currency or unit or "," in number or "." in number):
        return None, "year_or_value_unclear"            # "the S&P 500 level as 2059"
    scaled = scale != 1
    value *= scale
    if value <= 0:
        return None, "value_not_positive"
    if kind == "money" and not tol["currency"]:
        return None, "tolerance_kind_unclear"
    if (kind == "percent") != (tol["kind"] == "percent") or (kind == "count" and tol["kind"] == "money"):
        return None, "tolerance_kind_differs"
    if scaled and kind != "percent" and not tol["scaled"]:
        return None, "tolerance_scale_unclear"          # "$30.8B (within +/- $0.5)": 50 cents?
    if unit == "bps" and tol["unit"] != "bps":
        return None, "tolerance_unit_differs"           # "425 bps (within +/- 1%)"
    if kind == "count" and tol["scaled"] and re.fullmatch(r"[A-Za-z]{1,3}", following):
        return None, "tolerance_unit_differs"           # "5,000 kg (within +/- 2k)"
    if kind == "count" and tol["noun"] and not re.match(
            re.escape(tol["noun"]) + r"(?![A-Za-z])", claim[b:].lstrip()):
        return None, "tolerance_unit_differs"           # "5000 W (within +/- 0.5 kW)", "MW" and "mW"
    if tol["value"] >= value:
        return None, "tolerance_not_smaller_than_value"
    decimals = len(number.split(".")[1]) if "." in number else 0
    item = {
        "claim": claim, "span": [a, b], "kind": kind, "unit": _UNIT_OF[kind],
        "written": {"sign": m.group("sign") or "", "currency": "$" if currency else "",
                    "number": number, "unit_text": unit_text, "scale": _plain(scale),
                    "decimals": decimals},
        "value": _plain(value), "tolerance": _plain(tol["value"]),
        "tolerance_text": tm.group("tol"),
        "step": _plain(Decimal(1).scaleb(-decimals) * scale),
    }
    if kind == "percent" and tol["percent_sign"]:
        # "5.31% (within +/- 0.1%)": read as percentage points, not as a share of the value
        item["percent_tolerance_read_as_points"] = True
    return item, None


def _plain(d: Decimal) -> str:
    """A decimal written out in full: no exponent, no trailing zeros."""
    s = format(d.normalize(), "f")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------------ scan

@dataclass
class ScanResult:
    counts: dict
    items: list
    receipt: dict = field(repr=False)

    def to_dict(self) -> dict:
        import copy
        return copy.deepcopy(self.receipt)


def _where(pairs) -> dict:
    out = {}
    for p in pairs or ():
        if isinstance(p, (tuple, list)):
            k, v = p
        else:
            if "=" not in p:
                raise InputError(f"--where needs column=value, not {p!r}")
            k, v = p.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def scan_rubric(rubric: Union[str, Path], lead: Sequence[str] = DEFAULT_LEAD,
                where=None) -> ScanResult:
    """Find the criteria in the CSV file ``rubric`` that state one value and a tolerance.

    Columns: ``id`` and ``criterion`` are needed. ``weight`` (a number; criteria with a
    weight of zero or less are left out, because MET means something else for them) and
    ``group`` (a label, for example the task a criterion belongs to) are optional.
    ``where`` keeps only rows whose named columns hold the given values.
    """
    p = Path(rubric)
    if not p.is_file():
        raise InputError(f"file not found: {rubric}")
    raw, header, rows = _read_table(p)
    missing = [c for c in ("id", "criterion") if c not in header]
    if missing:
        raise InputError(f"{rubric}: column(s) {missing} are needed and are not in the header "
                         f"{header}")
    select = _where(where)
    unknown = [c for c in select if c not in header]
    if unknown:
        raise InputError(f"{rubric}: --where names column(s) {unknown} that are not in the header")
    lead = tuple(lead)
    has_weight, has_group = "weight" in header, "group" in header

    items, left_out, seen = [], {}, set()
    n = n_tol = 0
    groups, groups_tol, groups_ok = set(), set(), set()
    pos_weight, ok_weight = {}, {}          # per group (or one bucket): positive weight, checkable

    def leave(reason):
        left_out[reason] = left_out.get(reason, 0) + 1

    for line, cells in rows:
        if not cells:
            continue
        if len(cells) != len(header):
            raise InputError(f"{rubric}: line {line} has {len(cells)} cells, the header has "
                             f"{len(header)}")
        row = dict(zip(header, cells))
        n += 1
        ident, text = row["id"].strip(), row["criterion"].strip()
        if not ident or ident in seen:
            raise InputError(f"{rubric}: line {line}: the id is empty or used twice ({ident!r})")
        seen.add(ident)
        group = row["group"].strip() if has_group else ""
        groups.add(group)
        weight = None
        if has_weight:
            cell = row["weight"].strip()
            weight = Decimal(cell) if re.fullmatch(r"[+-]?\d{1,12}(?:\.\d{1,6})?", cell) else None
            if weight is None:
                raise InputError(f"{rubric}: line {line}: weight {row['weight']!r} is not a "
                                 f"number")
            if weight > 0:
                pos_weight[group] = pos_weight.get(group, Decimal(0)) + weight
        if not _MENTIONS_PLUS_OR_MINUS.search(text):
            continue
        n_tol += 1
        groups_tol.add(group)
        if (weight is not None and weight <= 0) or any(row[c].strip() != v for c, v in select.items()):
            leave("not_selected_or_not_a_positive_criterion")
            continue
        item, why = read_criterion(text, lead)
        if item is None:
            leave(why)
            continue
        item = dict({"id": ident, "line": line, "group": group,
                     "weight": _plain(weight) if weight is not None else None,
                     "criterion": text}, **item)
        items.append(item)
        groups_ok.add(group)
        if weight is not None:
            ok_weight[group] = ok_weight.get(group, Decimal(0)) + weight

    counts = {"criteria": n, "contain_within_plus_or_minus": n_tol, "checkable": len(items),
              "left_out": dict(sorted(left_out.items())),
              "percent_tolerance_read_as_points": sum(
                  bool(i.get("percent_tolerance_read_as_points")) for i in items)}
    if has_group:
        counts.update(groups=len(groups), groups_containing_within_plus_or_minus=len(groups_tol),
                      groups_with_a_checkable_criterion=len(groups_ok))
    if has_weight:
        total, ok = sum(pos_weight.values(), Decimal(0)), sum(ok_weight.values(), Decimal(0))
        shares = sorted(ok_weight[g] / pos_weight[g] for g in ok_weight if pos_weight.get(g))
        counts["weight"] = {
            "positive_total": _plain(total), "checkable": _plain(ok),
            "checkable_share": round(float(ok / total), 4) if total else None,
        }
        if has_group and shares:
            # over the groups that have a checkable criterion; the other groups have none
            counts["weight"]["groups_with_a_share"] = len(shares)
            counts["weight"]["share_within_a_group_min"] = round(float(shares[0]), 4)
            counts["weight"]["share_within_a_group_max"] = round(float(shares[-1]), 4)
    receipt = {
        "receipt": CONTRACTS_SCHEMA, "command": "rubric scan", "consilience_version": ENGINE_VERSION,
        "judge_check_version": __version__,
        "inputs": {"rubric": {"path": str(rubric), "sha256": sha256_bytes(raw), "bytes": len(raw)}},
        "options": {"lead": list(lead), "where": select},
        "result": {"counts": counts, "items": items},
    }
    receipt["sha256"] = sha256_json(receipt)
    return ScanResult(counts=counts, items=items, receipt=receipt)


def verify_scan(rec: dict, rubric_path=None, receipt_path=None):
    """Re-run a contracts file from its rubric. Returns (ok, steps, recomputed_sha256)."""
    steps = []
    recorded = rec.get("sha256")
    integrity = sha256_json({k: v for k, v in rec.items() if k != "sha256"})
    steps.append(("receipt hash", integrity == recorded, "matches its contents"
                  if integrity == recorded else "the file was changed after it was written"))
    try:
        stored = rec["inputs"]["rubric"]
        stored["path"], stored["sha256"]
    except (KeyError, TypeError):
        raise InputError("the contracts file does not name its rubric") from None
    p = _find(rubric_path or stored["path"], receipt_path)
    if p is None:
        steps.append(("rubric file", False, f"{stored['path']} not found; pass --data"))
        return False, steps, None
    got = sha256_bytes(p.read_bytes())
    same = got == stored["sha256"]
    steps.append(("rubric hash", same, f"{p} matches" if same else
                  f"{p} hashes to {got}, recorded {stored['sha256']}: the rubric changed"))
    opts = rec.get("options", {})
    again = scan_rubric(p, lead=opts.get("lead", DEFAULT_LEAD), where=list(opts.get("where", {}).items()))
    rerun = again.receipt["result"] == rec.get("result")
    steps.append(("re-run", rerun, "same result" if rerun else
                  "the re-run gives a different result from the file"))
    return all(ok for _, ok, _ in steps), steps, recorded if rerun and same else None


def _find(path, receipt_path) -> Optional[Path]:
    p = Path(path)
    if receipt_path is not None:
        q = Path(receipt_path).resolve().parent / p.name
        if q.is_file():
            return q                # the file beside the receipt is the one meant
    return p if p.is_file() else None


# ------------------------------------------------------------------ probes

def _exact(item: dict):
    return Decimal(item["value"]), Decimal(item["tolerance"])


def _write_number(v: Decimal, item: dict) -> str:
    """A new value written in the same unit and style as the criterion's own number.
    It keeps the criterion's number of decimal places and adds more only if needed."""
    w = item["written"]
    q = v / Decimal(w["scale"])
    dec = max(w["decimals"], max(0, -q.normalize().as_tuple().exponent))
    q = q.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)
    grouped = ("," in w["number"]) or Decimal(w["number"].replace(",", "")) < 1000
    s = f"{q:,.{dec}f}" if grouped else f"{q:.{dec}f}"
    return f"{w['sign']}{w['currency']}{s}{w['unit_text']}"


def _sentence(item: dict, token: Optional[str]) -> str:
    """The criterion's claim as a one-sentence response, with the number replaced by
    ``token`` (None: the criterion's own number). 'X as $5' becomes 'X was $5.'"""
    a, b = item["span"]
    claim = item["claim"]
    head = claim[:a]
    if head.endswith(" as "):
        head = head[:-4] + " was "
    s = (head + (claim[a:b] if token is None else token) + claim[b:]).strip()
    return s[0].upper() + s[1:] + ("" if s.endswith(".") else ".")


def _far(item: dict) -> Decimal:
    """A clearly wrong value: half as large again, rounded to the criterion's decimals;
    four tolerances away if that is not at least three tolerances away."""
    V, T = _exact(item)
    step = Decimal(item["step"])
    far = ((V * Decimal("1.5")) / step).quantize(Decimal(1), rounding=ROUND_HALF_UP) * step
    return V + 4 * T if far - V < 3 * T else far


def _other_unit(item: dict, v: Decimal):
    """The largest unit, other than the criterion's own, in which a dollar amount is
    between 1 and a million."""
    own = Decimal(item["written"]["scale"])
    cands = [(w, m) for w, m in _OTHER_UNITS if m != own and 1 <= v / m < 10 ** 6]
    return cands[-1] if cands else None


def _offset(label: str):
    """'+1.1' -> (Decimal('1.1'), False); '-0.9u' -> (Decimal('-0.9'), True); 'far' -> ('far', False)."""
    other = label.endswith("u")
    core = label[:-1] if other else label
    if core == "far":
        if other:
            raise InputError("offset 'faru' is not offered")
        return "far", False
    if not re.fullmatch(r"[+-]?\d{1,4}(?:\.\d{1,6})?", core):
        raise InputError(f"offset {label!r} is not a plain number of tolerances (for example "
                         f"0, +0.9, -1.1, far, or +1.1u for another unit)")
    return Decimal(core), other


def build_probes(contracts: Union[str, Path, dict], offsets: Sequence[str] = DEFAULT_OFFSETS,
                 *, comment: str = PROBES_COMMENT):
    """Probes for every item of a contracts file (a path, or the dict ``scan`` returned).

    ``offsets`` are distances from the reference in tolerances: ``0`` is the criterion's
    own value, ``+0.9`` just inside above it, ``-1.1`` just outside below it, ``far`` a
    clearly wrong value. A trailing ``u`` (``+1.1u``) writes a dollar amount in another
    unit ("$1,634k" as "$1.634 million").

    Returns (rows, skipped, csv_text): rows are dicts with ``PROBE_COLUMNS``; ``skipped``
    counts probes that could not be written (a value that would not be positive, no
    other unit to write it in).
    """
    if isinstance(contracts, (str, Path)):
        p = Path(contracts)
        if not p.is_file():
            raise InputError(f"file not found: {contracts}")
        import json
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise InputError(f"{contracts}: not JSON: {exc}") from None
    else:
        rec = contracts
    if not isinstance(rec, dict) or rec.get("receipt") != CONTRACTS_SCHEMA:
        raise InputError(f"not a contracts file (expected \"receipt\": \"{CONTRACTS_SCHEMA}\")")
    try:
        contract_items = rec["result"]["items"]
        lead = tuple((rec.get("options") or {}).get("lead") or DEFAULT_LEAD)
        seen_ids = set()
        for it in contract_items:
            again, _ = read_criterion(it["criterion"], lead)
            if again is None or any(it.get(k) != v for k, v in again.items()) \
                    or not isinstance(it["id"], str) or not isinstance(it["group"], str) \
                    or it["id"] in seen_ids:
                raise ValueError(it.get("id"))
            seen_ids.add(it["id"])
    except (KeyError, TypeError, ValueError, AttributeError):
        raise InputError("the contracts file is damaged or was edited: an item is not what the "
                         "reader makes of its criterion") from None
    labels = [str(o).strip() for o in offsets]
    if len(set(labels)) != len(labels) or not labels:
        raise InputError("offsets must be given once each, and at least one")
    parsed = [(lab,) + _offset(lab) for lab in labels]
    rows, skipped = [], {}
    with localcontext() as ctx:
        ctx.prec = _PRECISION
        _fill_probes(contract_items, parsed, rows, skipped)
    buf = io.StringIO()
    buf.write(comment)
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(PROBE_COLUMNS)
    for r in rows:
        w.writerow([r[c] for c in PROBE_COLUMNS])
    return rows, dict(sorted(skipped.items())), buf.getvalue()


def _fill_probes(contract_items, parsed, rows, skipped):
    for item in contract_items:
        V, T = _exact(item)
        for label, k, other in parsed:
            v = _far(item) if k == "far" else V + k * T
            if v <= 0:
                skipped[f"{label}:value_not_positive"] = skipped.get(f"{label}:value_not_positive", 0) + 1
                continue
            if other:
                unit = _other_unit(item, v) if item["kind"] == "money" else None
                if unit is None:
                    skipped[f"{label}:no_other_unit"] = skipped.get(f"{label}:no_other_unit", 0) + 1
                    continue
                word, m = unit
                q = (v / m).normalize()
                dec = max(0, -q.as_tuple().exponent)
                text = _sentence(item, f"${q:,.{dec}f}{word}")
            else:
                text = _sentence(item, None if k == 0 else _write_number(v, item))
            rows.append({
                "probe_id": f"{item['id']}@{label}", "item": item["id"], "cluster": item["group"],
                "criterion": item["criterion"], "response": text, "offset": label,
                "stated_value": _plain(v), "stated_unit": item["unit"],
                "reference_value": item["value"], "reference_unit": item["unit"],
                "tolerance": item["tolerance"], "reference_step": item["step"],
                "right_verdict": "met" if abs(v - V) <= T else "unmet",
            })


def probes_receipt(contracts_path, contracts_rec: dict, offsets, rows, skipped, csv_text: str,
                   out_path) -> dict:
    data = csv_text.encode("utf-8")
    receipt = {
        "receipt": PROBES_SCHEMA, "command": "rubric probes", "consilience_version": ENGINE_VERSION,
        "judge_check_version": __version__,
        "inputs": {"contracts": {"path": str(contracts_path), "sha256": contracts_rec.get("sha256")}},
        "options": {"offsets": [str(o) for o in offsets]},
        "result": {"probes": len(rows), "items": len({r["item"] for r in rows}), "skipped": skipped,
                   "output": {"path": str(out_path), "sha256": sha256_bytes(data), "bytes": len(data)}},
    }
    receipt["sha256"] = sha256_json(receipt)
    return receipt


def verify_probes(rec: dict, contracts_path=None, receipt_path=None):
    """Re-build a probes file from its contracts file. Returns (ok, steps, recomputed).

    The receipt ties the probes to a contracts file; the contracts file ties itself to
    the rubric (``verify`` it too if the rubric may have changed)."""
    import json
    steps = []
    recorded = rec.get("sha256")
    integrity = sha256_json({k: v for k, v in rec.items() if k != "sha256"})
    steps.append(("receipt hash", integrity == recorded, "matches its contents"
                  if integrity == recorded else "the receipt was edited after it was written"))
    try:
        stored, out, offsets = rec["inputs"]["contracts"], rec["result"]["output"], rec["options"]["offsets"]
        stored["path"], stored["sha256"], out["path"], out["sha256"]
    except (KeyError, TypeError):
        raise InputError("the probes receipt is damaged: a field is missing") from None
    p = _find(contracts_path or stored["path"], receipt_path)
    if p is None:
        steps.append(("contracts file", False, f"{stored['path']} not found; pass --data"))
        return False, steps, None
    try:
        contracts = json.loads(p.read_text(encoding="utf-8"))
        actual = sha256_json({k: v for k, v in contracts.items() if k != "sha256"})
    except (ValueError, AttributeError):
        steps.append(("contracts file", False, f"{p} is not a contracts file"))
        return False, steps, None
    same = actual == stored["sha256"] == contracts.get("sha256")
    steps.append(("contracts hash", same, f"{p} matches" if same else
                  f"{p} is not the contracts file the probes were built from, or was edited"))
    rerun = False
    for comment in (PROBES_COMMENT, PROBES_COMMENT_AS_FIRST_WRITTEN):
        try:
            rows, skipped, text = build_probes(contracts, offsets, comment=comment)
        except InputError as exc:
            steps.append(("re-run", False, str(exc)))
            return False, steps, None
        again = probes_receipt(stored["path"], contracts, offsets, rows, skipped, text, out["path"])
        rerun = again["result"] == rec["result"] and again["options"] == rec["options"]
        if rerun:
            break
    steps.append(("re-run", rerun, "the same probes, byte for byte" if rerun else
                  "the re-run gives different probes from the ones recorded"))
    q = _find(out["path"], receipt_path)
    on_disk = q is not None and sha256_bytes(q.read_bytes()) == out["sha256"]
    steps.append(("probes file", on_disk, f"{q} matches" if on_disk else
                  (f"{q} is not the file that was written" if q is not None else
                   f"{out['path']} was not found beside the receipt")))
    return all(ok for _, ok, _ in steps), steps, recorded if rerun and same else None


# ------------------------------------------------------------------ table

def probe_table(probes: Union[str, Path], verdicts: Union[str, Path], *,
                comment: str = TABLE_COMMENT):
    """Join a grader's verdicts on the probes into the table ``check`` reads.

    ``verdicts`` is a CSV file with the columns ``probe_id`` and ``verdict`` (met/unmet,
    pass/fail, yes/no, 1/0). Optional: ``call`` (a label when one probe was graded more
    than once) and ``context`` (a label when the probe was shown in some setting, for
    example inside a long report; such rows are counted as their own group).

    Returns (csv_text, summary). The right verdict is not copied into the table;
    ``check`` works it out from the numbers. (The ``group`` column is the probe's
    distance from the reference, kept for counting; ``check`` does not decide by it.)
    """
    pp, vp = Path(probes), Path(verdicts)
    for x in (pp, vp):
        if not x.is_file():
            raise InputError(f"file not found: {x}")
    _, ph, prows = _read_table(pp)
    missing = [c for c in PROBE_COLUMNS if c not in ph]
    if missing:
        raise InputError(f"{probes}: not a probes file (column(s) {missing} missing)")
    by_id = {}
    for line, cells in prows:
        if not cells:
            continue
        if len(cells) != len(ph):
            raise InputError(f"{probes}: line {line} has {len(cells)} cells, the header has {len(ph)}")
        r = dict(zip(ph, cells))
        if r["probe_id"] in by_id:
            raise InputError(f"{probes}: line {line}: probe {r['probe_id']} appears twice")
        by_id[r["probe_id"]] = r
    _, vh, vrows = _read_table(vp)
    missing = [c for c in ("probe_id", "verdict") if c not in vh]
    if missing:
        raise InputError(f"{verdicts}: column(s) {missing} are needed and are not in the header {vh}")
    out, unknown, seen, counter, graded, labelled = [], [], set(), {}, set(), {}
    for line, cells in vrows:
        if not cells:
            continue
        if len(cells) != len(vh):
            raise InputError(f"{verdicts}: line {line} has {len(cells)} cells, the header has {len(vh)}")
        v = dict(zip(vh, cells))
        pid = v["probe_id"].strip()
        if pid not in by_id:
            unknown.append(pid)
            continue
        p = by_id[pid]
        context = v.get("context", "").strip()
        key = (pid, context)
        call = v.get("call", "").strip()
        if labelled.setdefault(key, bool(call)) != bool(call):
            raise InputError(f"{verdicts}: line {line}: give a call label for every verdict on "
                             f"{pid} or for none")
        if not call:
            call = str(counter.get(key, 0))
        counter[key] = counter.get(key, 0) + 1
        ident = f"{pid}{':' + context if context else ''}#{call}"
        if ident in seen:
            raise InputError(f"{verdicts}: line {line}: {ident} is given twice")
        seen.add(ident)
        graded.add(pid)
        out.append([ident, p["reference_value"], p["reference_unit"],
                    f"{p['tolerance']} {p['reference_unit']}", p["stated_value"], p["stated_unit"],
                    v["verdict"].strip(), p["offset"] + (":" + context if context else ""),
                    p["item"], p["cluster"], p["reference_step"]])
    if unknown:
        raise InputError(f"{verdicts}: {len(unknown)} verdict(s) name a probe that is not in "
                         f"{probes}, for example {unknown[:3]}")
    out.sort(key=lambda r: (r[7], r[8], r[0]))
    buf = io.StringIO()
    buf.write(comment)
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(TABLE_COLUMNS)
    w.writerows(out)
    return buf.getvalue(), {"rows": len(out), "probes": len(by_id), "probes_graded": len(graded),
                            "probes_without_a_verdict": len(by_id) - len(graded)}
