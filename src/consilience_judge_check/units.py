"""Currency codes as units, on top of the Consilience engine.

The engine reads units with pint and treats a count word ("3 cells") as an amount of its
own kind: not comparable with another kind, and written without a prefix. This module
adds five currency codes to that same rule: ``USD``, ``EUR``, ``GBP``, ``INR`` and
``JPY``. An amount in one is not comparable with an amount in another (an exchange rate
is not a unit conversion), and no prefix is read: write the full amount in ``USD``, not
``kUSD``.

How. Two things are added to the engine when this package is imported, and nothing else
in it is changed:

* each code is defined in the engine's unit registry as a unit of its own kind;
* each code is added to the engine's list of words that take no prefix, so the engine
  itself refuses ``kUSD`` wherever it reads a unit: in a unit cell, inside a value cell,
  or in a tolerance however it is spaced.
"""
from __future__ import annotations

import consilience.units as _engine_units
from consilience.units import UREG

CURRENCY_UNITS = ("USD", "EUR", "GBP", "INR", "JPY")


def register_currencies() -> None:
    """Teach the engine the currency codes. Safe to call twice, and a no-op for any code
    the engine already knows."""
    for word in CURRENCY_UNITS:
        if word not in UREG:
            UREG.define(f"{word} = [{word}]")
    missing = tuple(w for w in CURRENCY_UNITS if w not in _engine_units.COUNT_UNITS)
    if missing:
        _engine_units.COUNT_UNITS = tuple(_engine_units.COUNT_UNITS) + missing


register_currencies()

__all__ = ["CURRENCY_UNITS", "register_currencies"]
