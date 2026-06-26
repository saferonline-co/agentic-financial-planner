"""TDD: cross-cutting invariants that must hold across scenarios + legacy ballpark."""
import pytest
from finmodel import schema, engine
from finmodel.returns import DeterministicReturns, StochasticReturns

SCENARIOS = ["recommended", "flat_baseline", "retire_earlier", "spend_lower",
             "rent_forever", "inheritance_zero", "pensions_indexed"]


@pytest.mark.parametrize("name", SCENARIOS)
def test_reserve_floor_never_drawn(name):
    cfg = schema.load_config(scenario=name)
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"))
    floor = cfg.reserve_floor
    for r in rows:
        assert r.accounts["cash"] >= floor - 1.0, f"{name} {r.year} cash<{floor}"


@pytest.mark.parametrize("name", SCENARIOS)
def test_person1_super_locked_until_access_year(name):
    cfg = schema.load_config(scenario=name)
    access = cfg.accounts["person1_super"].access_year
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"),
                      inheritance_variant="zero", spending_strategy="constant_real")
    # before access year, person1_super must be monotonically non-decreasing (only grows)
    prev = None
    for r in rows:
        if r.year < access and prev is not None:
            assert r.accounts["person1_super"] >= prev - 1.0
        prev = r.accounts["person1_super"]


def test_opening_reconciles_all_scenarios():
    for name in SCENARIOS:
        schema.load_config(scenario=name).validate()


def test_today_money_identity_holds():
    cfg = schema.load_config()
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"))
    for r in rows:
        assert r.net_worth_today == pytest.approx(r.net_worth_nominal / r.infl)


def test_legacy_mode_runs_and_is_positive():
    # Legacy mode uses flat per-account returns (each account's legacy_return) and
    # skips the super-earnings tax — a simple deterministic projection. Sanity-check
    # that it completes without depleting and produces a positive terminal net worth.
    cfg = schema.load_config()
    rows = engine.run(cfg, DeterministicReturns(cfg, "central", legacy=True), legacy=True)
    terminal = rows[-1].net_worth_today
    assert not rows[-1].depleted
    assert terminal > 0
