"""FCA-style deterministic stress overlays (TR24/1: model the bad cases).

Each overlay re-runs the deterministic central case under an adverse change and
reports terminal net worth (today's money) and whether the plan depleted:
  * year1_crash    — equity shock in the first retirement year (sequence risk)
  * sustained_low  — every asset-class mean derated (lost-decade world)
  * high_inflation — higher CPI for the whole projection
  * longevity_tail — extend the horizon to a later age
"""
from __future__ import annotations

from dataclasses import dataclass

from . import engine, schema
from .events import resolve_events, retirement_year
from .returns import DeterministicReturns


@dataclass
class StressResult:
    name: str
    terminal_today: float
    depleted: bool
    final_year: int


class _ShockProvider:
    """Deterministic returns with a one-year equity crash overlaid."""

    def __init__(self, cfg, shock_year: int, equity_return: float):
        self._base = DeterministicReturns(cfg, "central")
        self._shock_year = shock_year
        self._equity_return = equity_return

    def account_rate(self, account, year):
        if year == self._shock_year and account.allocation.get("equity", 0) > 0:
            w = account.allocation
            # crash the equity sleeve; other sleeves keep their central rate
            other = sum(v for k, v in w.items() if k != "equity")
            base = self._base.account_rate(account, year)
            non_equity = (base if other == 0 else
                          self._base.account_rate(account, year))
            return w["equity"] * self._equity_return + (1 - w["equity"]) * (
                non_equity / (1 - w["equity"]) if w["equity"] < 1 else 0.0)
        return self._base.account_rate(account, year)


class _HouseShockProvider:
    """Deterministic returns with a one-off house-price drop in `shock_year`."""

    def __init__(self, cfg, shock_year: int, house_return: float):
        self._base = DeterministicReturns(cfg, "central")
        self._shock_year = shock_year
        self._house_return = house_return

    def account_rate(self, account, year):
        if account.name == "house" and year == self._shock_year:
            return self._house_return
        return self._base.account_rate(account, year)


def _terminal(cfg, provider) -> StressResult:
    rows = engine.run(cfg, provider)
    last = rows[-1]
    return last


def run(cfg) -> list[StressResult]:
    out: list[StressResult] = []
    base_rows = engine.run(cfg, DeterministicReturns(cfg, "central"))
    bl = base_rows[-1]
    out.append(StressResult("base", bl.net_worth_today, bl.depleted, bl.year))

    for ov in cfg.stress.get("overlays", []):
        name, typ = ov["name"], ov["type"]
        c = schema.clone(cfg)
        if typ == "shock_year":
            sy = retirement_year(c) + ov.get("year_offset", 1) - 1
            rows = engine.run(c, _ShockProvider(c, sy, ov["equity_return"]))
        elif typ == "derate":
            for ac in c.assumptions["cma"]["asset_classes"].values():
                ac["mean"] += ov["amount"]
            for acc in c.accounts.values():
                if acc.legacy_return is not None:
                    acc.legacy_return += ov["amount"]
            rows = engine.run(c, DeterministicReturns(c, "central"))
        elif typ == "inflation_shock":
            c.assumptions["inflation"]["cpi"] = ov["cpi"]
            rows = engine.run(c, DeterministicReturns(c, "central"))
        elif typ == "extend_horizon":
            c.people["longevity_age"] = ov["to_age"]
            rows = engine.run(c, DeterministicReturns(c, "central"))
        elif typ == "house_shock":
            if c.house is None:
                continue  # no home to shock (rent-forever)
            buy = resolve_events(c).get("house_purchase")
            if buy is None:
                continue
            sy = buy + ov.get("year_offset", 1)
            rows = engine.run(c, _HouseShockProvider(c, sy, ov["house_return"]))
        elif typ == "aged_care_portfolio":
            # Care fees hit the investible pool, not the ring-fenced house, at a
            # fuller cost over longer episodes (realistic means-tested-care tail).
            c.aged_care["funded_from"] = "portfolio"
            c.aged_care["incremental_fraction"] = ov.get(
                "incremental_fraction", c.aged_care["incremental_fraction"])
            c.aged_care["episode_years"] = ov.get(
                "episode_years", c.aged_care["episode_years"])
            rows = engine.run(c, DeterministicReturns(c, "central"))
        last = rows[-1]
        out.append(StressResult(name, last.net_worth_today, last.depleted, last.year))
    return out
