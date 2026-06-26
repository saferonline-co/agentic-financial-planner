"""Deterministic complement metrics — chiefly the actuarial funded ratio.

Funded ratio = PV(assets + reliable income) / PV(spending liabilities), both
discounted at an AUD real risk-free rate (LDI convention: a near-certain spending
liability is discounted at a risk-free rate, not the risky portfolio return).
Computed in today's money over the retirement horizon.
"""
from __future__ import annotations

from . import engine, spending as spend_mod
from .events import retirement_year
from .returns import DeterministicReturns
from .schema import Config


def funded_ratio(cfg: Config, rows: list, *,
                 spending_strategy: str | None = None,
                 inheritance_variant: str | None = None) -> float:
    """Funded ratio at retirement: PV(assets + pensions) / PV(spending)."""
    retire = retirement_year(cfg)
    horizon = cfg.horizon_year
    rfr = cfg.assumptions["real_risk_free"]
    cpi = cfg.assumptions["inflation"]["cpi"]
    older = cfg.older_partner
    strategy = spending_strategy or cfg.raw["retirement_spending"]["strategy"]
    base = cfg.raw["retirement_spending"]["base"]

    # Assets at retirement (investible pool, today's money) — the ring-fenced
    # house is excluded (it funds aged care, not everyday spending).
    retire_row = next(r for r in rows if r.year == retire)
    assets = retire_row.drawpool_today

    pv_income = 0.0
    pv_spend = 0.0
    for t, year in enumerate(range(retire, horizon + 1)):
        disc = (1 + rfr) ** t
        # reliable income: frozen Foreign pensions deflated to today's money
        infl = (1 + cpi) ** (year - cfg.start_year)
        pension_today = engine._pension_income(cfg, year, infl) / infl
        older_age = cfg.age(older, year)
        if strategy in ("blanchett_smile", "constant_real"):
            spend_today = spend_mod.real_spend(strategy, cfg, base=base, older_age=older_age)
        else:
            spend_today = base
        pv_income += pension_today / disc
        pv_spend += spend_today / disc

    return (assets + pv_income) / pv_spend
