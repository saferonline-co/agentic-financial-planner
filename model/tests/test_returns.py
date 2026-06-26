"""TDD: deterministic (central/band) and stochastic return providers."""
import numpy as np
import pytest
from finmodel import schema, returns


@pytest.fixture
def cfg():
    return schema.load_config()


def test_geometric_from_arithmetic():
    # geo ~= mean - sd^2/2
    assert returns.geometric_from_arithmetic(0.088, 0.17) == pytest.approx(0.07355, abs=1e-4)
    assert returns.geometric_from_arithmetic(0.045, 0.06) == pytest.approx(0.0432, abs=1e-4)


def test_deterministic_central_from_allocation(cfg):
    p = returns.DeterministicReturns(cfg, band="central")
    etf = cfg.accounts["etf"]
    ac = cfg.assumptions["cma"]["asset_classes"]
    # 0.90*equity_geo + 0.10*bond_geo, derived from config (tracks CMA changes)
    eq_geo = returns.geometric_from_arithmetic(ac["equity"]["mean"], ac["equity"]["sd"])
    bd_geo = returns.geometric_from_arithmetic(ac["bond"]["mean"], ac["bond"]["sd"])
    expected = 0.90 * eq_geo + 0.10 * bd_geo
    assert p.account_rate(etf, 2030) == pytest.approx(expected, abs=1e-3)


def test_deterministic_band_shifts_central(cfg):
    central = returns.DeterministicReturns(cfg, band="central")
    low = returns.DeterministicReturns(cfg, band="low")
    high = returns.DeterministicReturns(cfg, band="high")
    etf = cfg.accounts["etf"]
    c = central.account_rate(etf, 2030)
    assert low.account_rate(etf, 2030) == pytest.approx(c - 0.03, abs=1e-6)
    assert high.account_rate(etf, 2030) == pytest.approx(c + 0.03, abs=1e-6)


def test_legacy_mode_uses_flat_account_returns(cfg):
    p = returns.DeterministicReturns(cfg, band="central", legacy=True)
    assert p.account_rate(cfg.accounts["etf"], 2030) == pytest.approx(0.07)
    assert p.account_rate(cfg.accounts["cash"], 2030) == pytest.approx(0.04)
    assert p.account_rate(cfg.accounts["person1_super"], 2030) == pytest.approx(0.067)


def test_stochastic_is_reproducible_with_seed(cfg):
    a = returns.StochasticReturns(cfg, seed=123)
    b = returns.StochasticReturns(cfg, seed=123)
    etf = cfg.accounts["etf"]
    ra = [a.account_rate(etf, y) for y in range(2026, 2073)]
    rb = [b.account_rate(etf, y) for y in range(2026, 2073)]
    assert ra == rb


def test_stochastic_mean_in_neighbourhood_of_arithmetic(cfg):
    # Across many seeds the ETF yearly return should average near its arithmetic
    # blend (0.9*equity_mean + 0.1*bond_mean), derived from config.
    ac = cfg.assumptions["cma"]["asset_classes"]
    expected = 0.90 * ac["equity"]["mean"] + 0.10 * ac["bond"]["mean"]
    etf = cfg.accounts["etf"]
    rng_means = []
    for s in range(400):
        p = returns.StochasticReturns(cfg, seed=s)
        rng_means.append(p.account_rate(etf, 2040))
    assert np.mean(rng_means) == pytest.approx(expected, abs=0.01)


def test_stochastic_rate_never_below_minus_one(cfg):
    etf = cfg.accounts["etf"]
    for s in range(200):
        p = returns.StochasticReturns(cfg, seed=s)
        for y in range(2026, 2073):
            assert p.account_rate(etf, y) > -1.0


# ---- home-specific growth schedule (2026-06 housing repricing) ----

def _house(cfg):
    return schema.Account("house", "property", 0.0, "joint",
                          cfg.start_year, {"property": 1.0})


def test_house_growth_schedule_regimes(cfg):
    cpi = cfg.assumptions["inflation"]["cpi"]  # 0.025
    # softer early real growth (+1% real), then the long-run trend (+2% real).
    assert returns.house_central_nominal(cfg, 2026) == pytest.approx(cpi + 0.01)
    assert returns.house_central_nominal(cfg, 2030) == pytest.approx(cpi + 0.01)
    assert returns.house_central_nominal(cfg, 2031) == pytest.approx(cpi + 0.02)  # trend
    assert returns.house_central_nominal(cfg, 2072) == pytest.approx(cpi + 0.02)


def test_house_growth_factor_compounds_schedule(cfg):
    cpi = cfg.assumptions["inflation"]["cpi"]
    # Price multiple at purchase year = growth over [start, year-1].
    assert returns.house_growth_factor(cfg, 2026) == pytest.approx(1.0)              # buy today
    assert returns.house_growth_factor(cfg, 2027) == pytest.approx(1 + cpi + 0.01)   # after 2026
    assert returns.house_growth_factor(cfg, 2028) == pytest.approx((1 + cpi + 0.01) ** 2)


def test_deterministic_house_uses_schedule_not_property_cma(cfg):
    det = returns.DeterministicReturns(cfg, "central")
    h = _house(cfg)
    cpi = cfg.assumptions["inflation"]["cpi"]
    # house rate follows the schedule, NOT the property CMA geometric.
    assert det.account_rate(h, 2037) == pytest.approx(cpi + 0.02)   # long-run trend regime
    assert det.account_rate(h, 2026) == pytest.approx(cpi + 0.01)   # softer early regime
    # band still shifts it (central cpi+0.02, low = central - 0.03 band)
    low = returns.DeterministicReturns(cfg, "low")
    assert low.account_rate(h, 2037) == pytest.approx(cpi - 0.01)


def test_stochastic_house_recentred_on_schedule(cfg):
    # MC house path: mean near the schedule (2% real in 2050), but still volatile.
    h = _house(cfg)
    target = returns.house_central_nominal(cfg, 2050)
    rates = [returns.StochasticReturns(cfg, seed=s).account_rate(h, 2050) for s in range(400)]
    assert np.mean(rates) == pytest.approx(target, abs=0.02)
    assert np.std(rates) > 0.02   # not collapsed to a constant
