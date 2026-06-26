"""TDD: FCA-style stress overlays."""
import pytest
from finmodel import schema, stress


@pytest.fixture
def cfg():
    return schema.load_config()


def test_stress_returns_all_overlays_plus_base(cfg):
    res = stress.run(cfg)
    names = {r.name for r in res}
    assert "base" in names
    assert {"year1_crash", "sustained_low", "high_inflation", "longevity_tail"} <= names


def test_stresses_are_not_kinder_than_base(cfg):
    res = {r.name: r for r in stress.run(cfg)}
    base = res["base"].terminal_today
    # A sustained-low-return world should leave less terminal wealth than base.
    assert res["sustained_low"].terminal_today < base


def test_clone_is_independent(cfg):
    c2 = schema.clone(cfg)
    c2.assumptions["inflation"]["cpi"] = 0.99
    assert cfg.assumptions["inflation"]["cpi"] == 0.025


# ---- house-price-fall overlay (2026-06 housing repricing) ----

def test_house_shock_overlays_present_and_hurt(cfg):
    res = {r.name: r for r in stress.run(cfg)}
    assert "house_correction_30" in res and "house_correction_20" in res
    base = res["base"].terminal_today
    # a 30% home fall must leave less terminal wealth than the base case...
    assert res["house_correction_30"].terminal_today < base
    # ...and be at least as harsh as the 20% fall.
    assert res["house_correction_30"].terminal_today <= res["house_correction_20"].terminal_today


def test_house_shock_is_noop_when_renting():
    # rent_forever has no home: the overlay must be skipped, not crash.
    cfg = schema.load_config(scenario="rent_forever")
    names = {r.name for r in stress.run(cfg)}
    assert "house_correction_30" not in names
    assert "base" in names
