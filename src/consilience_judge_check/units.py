"""Currency codes as units, on top of the Consilience engine.

The engine reads units with pint and treats a count word ("3 cells") as an amount of its
own kind. This module adds five currency codes in the same way: ``USD``, ``EUR``,
``GBP``, ``INR`` and ``JPY``. An amount in one is not comparable with an amount in
another (an exchange rate is not a unit conversion), and no prefix is read: write the
full amount in ``USD``, not ``kUSD``.
"""
from __future__ import annotations

from typing import Optional

from consilience.units import UREG

CURRENCY_UNITS = ("USD", "EUR", "GBP", "INR", "JPY")


def register_currencies() -> None:
    """Teach the engine's unit registry the currency codes. Safe to call twice, and a
    no-op for any code the engine already knows."""
    for word in CURRENCY_UNITS:
        if word not in UREG:
            UREG.define(f"{word} = [{word}]")


def prefixed_currency(unit: str) -> Optional[str]:
    """The currency code, if ``unit`` writes one with a prefix (``kUSD``); else None."""
    text = (unit or "").strip()
    if not text or not any(word in text for word in CURRENCY_UNITS):
        return None
    try:
        parsed = UREG.parse_units(text)
    except Exception:           # not a unit at all: the engine reports that itself
        return None
    for name in parsed._units:
        for word in CURRENCY_UNITS:
            if name != word and name.endswith(word):
                return word
    return None


register_currencies()

__all__ = ["CURRENCY_UNITS", "prefixed_currency", "register_currencies"]
