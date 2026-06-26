"""TDD: Monte Carlo aggregation and metrics."""
import pytest
from finmodel import schema, montecarlo, metrics
from finmodel.returns import DeterministicReturns
from finmodel import engine


@pytest.fixture
def cfg():
    return schema.load_config()


def test_mc_result_shape(cfg):
    res = montecarlo.run(cfg, trials=200)
    assert res.trials == 200
    assert 0.0 <= res.p_sustains <= 1.0
    assert 0.0 <= res.p_capital_preserved <= res.p_sustains + 1e-9
    assert res.terminal_p10 <= res.terminal_p50 <= res.terminal_p90


def test_mc_reproducible_with_seed(cfg):
    a = montecarlo.run(cfg, trials=200)
    b = montecarlo.run(cfg, trials=200)
    assert a.p_sustains == b.p_sustains
    assert a.terminal_p50 == pytest.approx(b.terminal_p50)


def test_zero_inheritance_is_not_better_than_full(cfg):
    full = montecarlo.run(cfg, trials=400, inheritance_variant="full")
    zero = montecarlo.run(cfg, trials=400, inheritance_variant="zero")
    assert zero.p_sustains <= full.p_sustains + 0.02


def test_glidepath_beats_constant_real_at_same_base(cfg):
    glide = montecarlo.run(cfg, trials=400, spending_strategy="blanchett_smile")
    flat = montecarlo.run(cfg, trials=400, spending_strategy="constant_real")
    assert glide.p_sustains >= flat.p_sustains


def test_funded_ratio_deterministic(cfg):
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"))
    fr = metrics.funded_ratio(cfg, rows)
    assert fr > 0
    # Recommended path is comfortably funded in the central case.
    assert fr > 1.0


def test_funded_ratio_below_one_when_overspending(cfg):
    cfg.raw["retirement_spending"]["base"] = 400_000
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"),
                      inheritance_variant="zero", spending_strategy="constant_real")
    fr = metrics.funded_ratio(cfg, rows, spending_strategy="constant_real",
                              inheritance_variant="zero")
    assert fr < 1.0
