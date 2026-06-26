"""TDD: config loading, validation, age/horizon resolution, NW reconciliation."""
import pytest
from finmodel import schema


@pytest.fixture
def cfg():
    return schema.load_config()


def test_loads_base_config(cfg):
    assert cfg.meta["base_currency"] == "AUD"
    assert cfg.start_year == 2026


def test_opening_net_worth_reconciles(cfg):
    # Sum of account balances + tax liability must equal meta.reconcile_target.
    assert cfg.opening_net_worth() == pytest.approx(1_500_000, abs=1.0)


def test_horizon_year_from_horizon_person_longevity(cfg):
    # Person 1 b.1980, longevity 92 -> 2072 (the binding tail).
    assert cfg.horizon_year == 2072


def test_age_resolution(cfg):
    assert cfg.age("person2", 2031) == 63      # b.1968
    assert cfg.age("person1", 2036) == 56     # b.1980


def test_older_partner(cfg):
    assert cfg.older_partner == "person2"


def test_accounts_loaded_with_required_fields(cfg):
    assert set(cfg.accounts) >= {
        "cash", "etf", "person1_foreign_pension", "person2_foreign_pension",
        "person1_taxfree", "person1_super", "person2_super", "foreign_property",
    }
    a = cfg.accounts["person1_super"]
    assert a.wrapper == "super"
    assert a.owner == "person1"
    assert a.access_year == 2040
    assert a.balance == 250000
    assert a.allocation["equity"] == 0.75


def test_reserve_floor_is_within_cash(cfg):
    # Reserve is a behavioural floor inside cash, not an extra asset.
    assert cfg.reserve_floor == 80000
    assert cfg.accounts["cash"].balance >= cfg.reserve_floor


def test_validate_passes_on_base(cfg):
    cfg.validate()  # should not raise


def test_validate_catches_broken_reconciliation(cfg):
    cfg.accounts["cash"].balance += 5000
    with pytest.raises(ValueError, match="reconcile"):
        cfg.validate()


def test_pensions_frozen_by_default(cfg):
    assert cfg.pensions["person2"]["indexed"] is False
    assert cfg.pensions["person1"]["start_year"] == 2048   # Person 1 state-pension age 68 (b.1980)
