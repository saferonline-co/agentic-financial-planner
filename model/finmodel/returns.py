"""Return providers — the single dependency that splits deterministic from MC.

The engine asks `provider.account_rate(account, year)`. Two implementations:

* DeterministicReturns — central case (allocation-weighted geometric of the CMA
  arithmetic means), plus a low/intermediate/high band (+/- deterministic_band,
  FCA COBS 13). `legacy=True` uses each account's flat legacy_return for exact
  regression against the old scripts.
* StochasticReturns — one correlated lognormal path per asset class for the whole
  horizon, drawn from the arithmetic-mean CMAs and the correlation matrix; an
  account's rate is the allocation-weighted blend. Seeded for reproducibility.
"""
from __future__ import annotations

import math
from typing import Protocol

import numpy as np

from .schema import Account, Config


def geometric_from_arithmetic(mean: float, sd: float) -> float:
    """Geometric (compound) equivalent of an arithmetic mean: ~ mean - sd^2/2."""
    return mean - 0.5 * sd * sd


def house_central_nominal(cfg: Config, year: int) -> float:
    """Central expected NOMINAL growth of the family home in `year`.

    Reads the home-specific `house.growth` schedule (decoupled from the property
    CMA) — a list of regimes ordered by `until_year`, each giving either an
    absolute `nominal` rate or a `real` rate (nominal = real + cpi). The final,
    open-ended entry (no `until_year`) applies thereafter. Falls back to the
    property CMA geometric if no schedule is configured.
    """
    cpi = cfg.assumptions["inflation"]["cpi"]
    sched = cfg.house.get("growth") if cfg.house else None
    if not sched:
        p = cfg.assumptions["cma"]["asset_classes"]["property"]
        return geometric_from_arithmetic(p["mean"], p["sd"])
    chosen = sched[-1]
    for entry in sched:
        if entry.get("until_year") is not None and year <= entry["until_year"]:
            chosen = entry
            break
    return chosen["nominal"] if "nominal" in chosen else chosen["real"] + cpi


def house_growth_factor(cfg: Config, year: int) -> float:
    """Cumulative central nominal growth of the home from `start_year` to the start
    of `year` — the multiple on `target_price_today` giving the home's market price
    at a purchase in `year`. Compounds the schedule rate over [start, year-1], so a
    purchase at `start_year` pays today's price and later purchases reflect the
    intervening down-leg (matches the old `(1+rate)**(year-start)` factor count)."""
    factor = 1.0
    for y in range(cfg.start_year, year):
        factor *= 1.0 + house_central_nominal(cfg, y)
    return factor


class ReturnsProvider(Protocol):
    def account_rate(self, account: Account, year: int) -> float: ...


class DeterministicReturns:
    """Central / band / legacy deterministic returns."""

    def __init__(self, cfg: Config, band: str = "central", legacy: bool = False):
        self.cfg = cfg
        self.legacy = legacy
        ac = cfg.assumptions["cma"]["asset_classes"]
        self._geo = {k: geometric_from_arithmetic(v["mean"], v["sd"]) for k, v in ac.items()}
        delta = float(cfg.assumptions.get("deterministic_band", 0.0))
        self._shift = {"central": 0.0, "low": -delta, "high": +delta}[band]

    def account_rate(self, account: Account, year: int) -> float:
        if self.legacy:
            return float(account.legacy_return)
        if account.name == "house":
            return house_central_nominal(self.cfg, year) + self._shift
        base = sum(w * self._geo[a] for a, w in account.allocation.items())
        return base + self._shift


class StochasticReturns:
    """Correlated lognormal per-asset paths; account rate = allocation blend."""

    def __init__(self, cfg: Config, seed: int | None = None):
        self.cfg = cfg
        ac = cfg.assumptions["cma"]["asset_classes"]
        self.assets = list(ac.keys())
        means = np.array([ac[a]["mean"] for a in self.assets])
        sds = np.array([ac[a]["sd"] for a in self.assets])

        # lognormal log-space params for arithmetic mean m, sd s
        var_log = np.log(1.0 + (sds**2) / (1.0 + means) ** 2)
        sig_log = np.sqrt(var_log)
        mu_log = np.log(1.0 + means) - 0.5 * var_log

        corr = cfg.assumptions["cma"]["correlation"]
        C = np.array([[corr[a][b] for b in self.assets] for a in self.assets])
        cov_log = C * np.outer(sig_log, sig_log)

        start, horizon = cfg.start_year, cfg.horizon_year
        self.start = start
        n_years = horizon - start + 1
        rng = np.random.default_rng(seed)
        normals = rng.multivariate_normal(mu_log, cov_log, size=n_years)  # (years, assets)
        gross = np.exp(normals)
        self._rates = gross - 1.0  # (years, assets); always > -1
        self._idx = {a: i for i, a in enumerate(self.assets)}

    def asset_rate(self, asset: str, year: int) -> float:
        return float(self._rates[year - self.start, self._idx[asset]])

    def account_rate(self, account: Account, year: int) -> float:
        row = year - self.start
        if account.name == "house":
            # Recentre the correlated property draw onto the home's schedule: keep
            # its volatility/correlation (so the stochastic downside tail still
            # appears) but drop the property CMA drift in favour of the schedule.
            prop_mean = self.cfg.assumptions["cma"]["asset_classes"]["property"]["mean"]
            noise = self.asset_rate("property", year) - prop_mean
            return house_central_nominal(self.cfg, year) + noise
        return float(
            sum(w * self._rates[row, self._idx[a]] for a, w in account.allocation.items())
        )
