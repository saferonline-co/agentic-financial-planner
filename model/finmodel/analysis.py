"""Bundle a scenario's deterministic ledger + Monte Carlo + funded ratio."""
from __future__ import annotations

from dataclasses import dataclass

from . import engine, metrics, montecarlo
from .montecarlo import MCResult
from .returns import DeterministicReturns
from .schema import Config, load_config


@dataclass
class ScenarioResult:
    name: str
    cfg: Config
    rows: list           # deterministic central ledger (YearRow[])
    rows_low: list       # deterministic low band
    rows_high: list      # deterministic high band
    mc: MCResult
    funded_ratio: float
    terminal_today: float


def analyse(cfg: Config | None = None, *, scenario_name: str = "base",
            trials: int | None = None) -> ScenarioResult:
    if cfg is None:
        cfg = load_config(scenario=None if scenario_name in ("base",) else scenario_name)
    cfg.validate()
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"))
    rows_low = engine.run(cfg, DeterministicReturns(cfg, "low"))
    rows_high = engine.run(cfg, DeterministicReturns(cfg, "high"))
    mc = montecarlo.run(cfg, trials=trials)
    fr = metrics.funded_ratio(cfg, rows)
    return ScenarioResult(
        name=scenario_name, cfg=cfg, rows=rows, rows_low=rows_low, rows_high=rows_high,
        mc=mc, funded_ratio=fr, terminal_today=rows[-1].net_worth_today,
    )
