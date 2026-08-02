#!/usr/bin/env python3
"""Turning a pool hash rate reading into the text on the menu bar."""

# Multipliers onto TH/s, which is the unit the widget prefers to show.
TO_TERAHASH = {
    "Kh/s": 1e-9,
    "Mh/s": 1e-6,
    "Gh/s": 1e-3,
    "Th/s": 1.0,
    "TH/s": 1.0,
    "Ph/s": 1e3,
    "Eh/s": 1e6,
}

# Below this the reading is shown in its own unit instead. One tenth of a
# terahash reads better as 100 Gh/s than as 0.1 TH/s.
MIN_TERAHASH = 1.0


def format_hashrate(value, unit: str) -> str:
    """Hash rate as it appears on the menu bar.

    A reading large enough is converted to TH/s. A smaller one keeps the unit
    the pool used, and an unknown unit is passed through rather than guessed at.
    """
    if value is None:
        return "--"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "--"

    factor = TO_TERAHASH.get(unit)
    if factor is None:
        return f"{value:.1f}{unit}"

    terahash = value * factor
    if terahash >= MIN_TERAHASH:
        return f"{terahash:.1f}TH/s"
    return f"{value:.1f}{unit}"


def format_temperature(celsius) -> str:
    """Temperature as it appears on the menu bar."""
    return "--" if celsius is None else f"{celsius:.1f}"


def format_title(hashrate: str, temperature: str) -> str:
    """The whole menu bar entry."""
    return f"{hashrate} {temperature}°C"
