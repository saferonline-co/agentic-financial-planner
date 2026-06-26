"""Config loading, validation, and typed access.

Loads config/config.yaml (the single source of truth), optionally deep-merges a
named scenario override, and exposes a typed Config with age/horizon resolution
and an opening net-worth reconciliation check.
"""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class Account:
    name: str
    wrapper: str
    balance: float
    owner: str
    access_year: int                 # full / lump-sum access (condition of release met)
    allocation: dict[str, float]
    cost_base: float | None = None
    legacy_return: float | None = None
    sale_value: float | None = None
    # Transition-to-Retirement: from `ttr_access_year` (preservation age 60 while
    # still working) a super pot yields only a capped income stream (`ttr_max_pct`
    # of balance/yr) — NO lump sum — until `access_year` unlocks the full balance.
    ttr_access_year: int | None = None
    ttr_max_pct: float = 0.0


@dataclass
class Config:
    raw: dict[str, Any]
    meta: dict[str, Any]
    people: dict[str, Any]
    assumptions: dict[str, Any]
    accounts: dict[str, Account]
    liabilities: dict[str, Any]
    reserve_floor: float
    pensions: dict[str, Any]
    phases: list[dict[str, Any]]
    events: dict[str, Any]
    house: dict[str, Any] | None
    inheritance: dict[str, Any]
    spending_strategies: dict[str, Any]
    aged_care: dict[str, Any]
    tax: dict[str, Any]
    monte_carlo: dict[str, Any]
    stress: dict[str, Any]
    legacy: dict[str, Any] = field(default_factory=dict)

    # ----- derived -----
    @property
    def start_year(self) -> int:
        return int(self.meta["start_year"])

    @property
    def horizon_year(self) -> int:
        person = self.people["horizon_person"]
        return int(self.people[person]["dob"] + self.people["longevity_age"])

    @property
    def older_partner(self) -> str:
        return self.people["older_partner"]

    def age(self, person: str, year: int) -> int:
        return int(year - self.people[person]["dob"])

    def opening_net_worth(self) -> float:
        total = sum(a.balance for a in self.accounts.values())
        total += float(self.liabilities.get("tax_liability", 0.0))
        return total

    def validate(self) -> None:
        # Optional opening-balance-sheet reconciliation: if meta.reconcile_target
        # is set, the sum of account balances (+ tax_liability) must match it. Lets
        # you pin a known net worth as a typo guard; omit it (e.g. the skeleton
        # config) to skip the check entirely.
        target = self.meta.get("reconcile_target")
        if target is not None:
            nw = self.opening_net_worth()
            if abs(nw - float(target)) > 1.0:
                raise ValueError(
                    f"opening balance sheet does not reconcile: {nw:,.0f} "
                    f"vs target {float(target):,.0f}"
                )
        # every account must have a resolvable owner age basis
        for name, acc in self.accounts.items():
            if acc.owner not in ("joint",) and acc.owner not in self.people:
                raise ValueError(f"account {name} has unknown owner {acc.owner!r}")
        # horizon must be after start
        if self.horizon_year <= self.start_year:
            raise ValueError("horizon_year must be after start_year")


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursive dict merge; scenario scalars/lists win. Returns a new dict."""
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _build_accounts(raw_accounts: dict[str, Any]) -> dict[str, Account]:
    accounts: dict[str, Account] = {}
    for name, spec in raw_accounts.items():
        accounts[name] = Account(
            name=name,
            wrapper=spec["wrapper"],
            balance=float(spec["balance"]),
            owner=spec["owner"],
            access_year=int(spec["access_year"]),
            allocation=dict(spec.get("allocation", {})),
            cost_base=spec.get("cost_base"),
            legacy_return=spec.get("legacy_return"),
            sale_value=spec.get("sale_value"),
            ttr_access_year=spec.get("ttr_access_year"),
            ttr_max_pct=float(spec.get("ttr_max_pct", 0.0)),
        )
    return accounts


def clone(cfg: "Config") -> "Config":
    """Deep-copy a config (via its raw dict) for non-destructive mutation."""
    return from_dict(copy.deepcopy(cfg.raw))


def from_dict(raw: dict[str, Any]) -> Config:
    return Config(
        raw=raw,
        meta=raw["meta"],
        people=raw["people"],
        assumptions=raw["assumptions"],
        accounts=_build_accounts(raw["accounts"]),
        liabilities=raw.get("liabilities", {}),
        reserve_floor=float(raw.get("reserve_floor", 0.0)),
        pensions=raw["pensions"],
        phases=raw["phases"],
        events=raw["events"],
        house=raw.get("house"),
        inheritance=raw["inheritance"],
        spending_strategies=raw["spending_strategies"],
        aged_care=raw["aged_care"],
        tax=raw["tax"],
        monte_carlo=raw["monte_carlo"],
        stress=raw.get("stress", {}),
        legacy=raw.get("legacy", {}),
    )


def load_config(
    config_path: str | Path | None = None,
    scenario: str | None = None,
    scenarios_path: str | Path | None = None,
) -> Config:
    """Load base config; optionally deep-merge a named scenario override.

    With no explicit ``config_path``, the base file name defaults to
    ``personal/config.yaml`` (your private, git-ignored plan) but can be
    overridden via the ``FINMODEL_CONFIG`` env var (the test suite points this
    at ``config.test.yaml``)."""
    default_name = os.environ.get("FINMODEL_CONFIG", "personal/config.yaml")
    config_path = Path(config_path) if config_path else CONFIG_DIR / default_name
    with open(config_path) as fh:
        raw = yaml.safe_load(fh)

    if scenario:
        scenarios_path = (
            Path(scenarios_path) if scenarios_path else CONFIG_DIR / "scenarios.yaml"
        )
        with open(scenarios_path) as fh:
            scenarios = yaml.safe_load(fh) or {}
        overrides = (scenarios.get("scenarios") or {}).get(scenario)
        if overrides is None:
            raise KeyError(f"scenario {scenario!r} not found in {scenarios_path}")
        raw = _deep_merge(raw, overrides)

    return from_dict(raw)
