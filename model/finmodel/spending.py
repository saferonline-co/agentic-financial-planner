"""Retirement spending strategies. All return REAL (today's money) spend.

Default = blanchett_smile (the retirement spending smile / our glidepath).
Also: constant_real, vanguard_dynamic (ceiling/floor collar), guardrails
(Guyton-Klinger). Portfolio-pegged strategies take the current state as args.
"""
from __future__ import annotations

from .schema import Config


def blanchett_multiplier(age: int, params: dict) -> float:
    """Real multiplier of base: flat to flat_until_age, then -decline_rate/yr,
    floored at floor_multiplier."""
    flat_until = params["flat_until_age"]
    if age <= flat_until:
        return 1.0
    raw = 1.0 - params["decline_rate"] * (age - flat_until)
    return max(params["floor_multiplier"], raw)


def real_spend(strategy: str, cfg: Config, *, base: float, older_age: int) -> float:
    """Path-independent strategies (blanchett_smile, constant_real)."""
    if strategy == "blanchett_smile":
        params = cfg.spending_strategies["blanchett_smile"]
        return base * blanchett_multiplier(older_age, params)
    if strategy == "constant_real":
        return base
    raise ValueError(f"{strategy!r} is path-dependent; call its function directly")


def vanguard_dynamic(*, prev: float, portfolio: float, wr: float, params: dict) -> float:
    """Ceiling/floor collar on a target = wr x portfolio (Vanguard dynamic)."""
    target = wr * portfolio
    ceiling = prev * (1.0 + params["ceiling"])
    floor = prev * (1.0 + params["floor"])
    return min(ceiling, max(floor, target))


def guardrails(*, prev: float, portfolio: float, iwr: float, params: dict, years_remaining: int) -> float:
    """Guyton-Klinger capital-preservation / prosperity rails on current spend."""
    cwr = prev / portfolio
    new = prev
    if cwr > iwr * params["upper_rail"] and years_remaining > 15:
        new = prev * (1.0 - params["adjust"])
    elif cwr < iwr * params["lower_rail"]:
        new = prev * (1.0 + params["adjust"])
    return new
