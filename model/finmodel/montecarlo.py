"""Monte Carlo: run the engine over N correlated-lognormal return paths.

Aggregates the standard metrics: probability of success (never depletes),
probability capital preserved (terminal real pool >= fraction of starting pool),
and terminal net-worth percentiles (today's money).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import engine
from .events import retirement_year
from .returns import StochasticReturns
from .schema import Config


@dataclass
class MCResult:
    trials: int
    p_sustains: float
    p_capital_preserved: float
    terminal_p10: float
    terminal_p50: float
    terminal_p90: float
    median_depletion_year: int | None
    # terminal INVESTIBLE POOL (today's money) — the income-generating capital,
    # excluding the ring-fenced home. The honest basis for income sustainability.
    pool_p10: float = 0.0
    pool_p50: float = 0.0
    pool_p90: float = 0.0


def run(cfg: Config, *, trials: int | None = None,
        inheritance_variant: str | None = None,
        spending_strategy: str | None = None) -> MCResult:
    mc = cfg.monte_carlo
    trials = trials or mc["trials"]
    base_seed = mc.get("seed", 0)
    cap_frac = mc["capital_preserved_fraction"]
    retire = retirement_year(cfg)

    terminals: list[float] = []
    pool_terminals: list[float] = []
    sustains = 0
    preserved = 0
    depletion_years: list[int] = []

    for i in range(trials):
        provider = StochasticReturns(cfg, seed=base_seed + i)
        rows = engine.run(cfg, provider, inheritance_variant=inheritance_variant,
                          spending_strategy=spending_strategy)
        last = rows[-1]
        terminals.append(last.net_worth_after_tax_today)  # honest after-tax terminal
        pool_terminals.append(last.drawpool_today)        # investible pool ex-house
        if not last.depleted:
            sustains += 1
            start_pool = next(r.drawpool_today for r in rows if r.year == retire)
            if last.drawpool_today >= cap_frac * start_pool:
                preserved += 1
        else:
            depletion_years.append(last.year)

    arr = np.array(terminals)
    pool = np.array(pool_terminals)
    return MCResult(
        trials=trials,
        p_sustains=sustains / trials,
        p_capital_preserved=preserved / trials,
        terminal_p10=float(np.percentile(arr, 10)),
        terminal_p50=float(np.percentile(arr, 50)),
        terminal_p90=float(np.percentile(arr, 90)),
        median_depletion_year=(int(np.median(depletion_years)) if depletion_years else None),
        pool_p10=float(np.percentile(pool, 10)),
        pool_p50=float(np.percentile(pool, 50)),
        pool_p90=float(np.percentile(pool, 90)),
    )
