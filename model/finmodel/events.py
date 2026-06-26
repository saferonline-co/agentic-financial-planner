"""Event-year resolution and year->phase mapping.

Events are the single mechanism for time-keyed changes: phase boundaries,
retirement, house purchase, inheritance, super access, pension starts. Years are
config so changing one (e.g. person1_retires) cascades to every downstream phase.
"""
from __future__ import annotations

from typing import Any

from .schema import Config


def resolve_events(cfg: Config) -> dict[str, int]:
    """Map every event name to its absolute year."""
    return {name: int(spec["year"]) for name, spec in cfg.events.items()}


def retirement_year(cfg: Config) -> int:
    """Person 1's retirement = start of the decumulation phase / horizon binding age."""
    return int(cfg.events["person1_retires"]["year"])


def _phase_start_year(cfg: Config, phase: dict[str, Any], ev: dict[str, int]) -> int:
    from_event = phase["from_event"]
    return ev[from_event]


def phase_for_year(cfg: Config, year: int) -> dict[str, Any]:
    """Return the phase a year belongs to: the latest phase that has started.

    Using "latest start <= year" avoids inclusive/exclusive boundary edge cases
    and is robust when event years are moved by a scenario.
    """
    ev = resolve_events(cfg)
    started = [
        (p, _phase_start_year(cfg, p, ev))
        for p in cfg.phases
        if _phase_start_year(cfg, p, ev) <= year
    ]
    if not started:
        raise ValueError(f"no phase covers year {year}")
    # the one with the largest start year
    return max(started, key=lambda t: t[1])[0]


def events_of_type(cfg: Config, etype: str) -> list[dict[str, Any]]:
    """All event specs of a given type (e.g. 'super_access', 'pension_start')."""
    return [spec for spec in cfg.events.values() if spec.get("type") == etype]
