"""TDD: retirement spending strategies (real, today's money)."""
import pytest
from finmodel import schema, spending


@pytest.fixture
def cfg():
    return schema.load_config()


def test_blanchett_smile_curve(cfg):
    params = cfg.spending_strategies["blanchett_smile"]
    f = lambda age: spending.blanchett_multiplier(age, params)
    assert f(65) == pytest.approx(1.00)
    assert f(70) == pytest.approx(1.00)
    assert f(75) == pytest.approx(0.90)   # 1 - 0.02*5
    assert f(80) == pytest.approx(0.80)
    assert f(95) == pytest.approx(0.75)   # floored


def test_real_spend_blanchett_pegged_to_older_partner(cfg):
    # Person 2 (older) age 75 in 2042 -> 0.90 * 130k
    amt = spending.real_spend("blanchett_smile", cfg, base=130_000, older_age=75)
    assert amt == pytest.approx(117_000)


def test_real_spend_constant(cfg):
    amt = spending.real_spend("constant_real", cfg, base=130_000, older_age=85)
    assert amt == pytest.approx(130_000)


def test_vanguard_dynamic_clips_to_collar(cfg):
    p = cfg.spending_strategies["vanguard_dynamic"]
    # prev 100k, wr 5%
    assert spending.vanguard_dynamic(prev=100_000, portfolio=2_000_000, wr=0.05, params=p) == pytest.approx(100_000)
    assert spending.vanguard_dynamic(prev=100_000, portfolio=2_400_000, wr=0.05, params=p) == pytest.approx(105_000)  # ceiling +5%
    assert spending.vanguard_dynamic(prev=100_000, portfolio=1_600_000, wr=0.05, params=p) == pytest.approx(98_500)   # floor -1.5%


def test_guardrails_cuts_when_upper_rail_breached(cfg):
    p = cfg.spending_strategies["guardrails"]
    # CWR = 0.06, IWR = 0.04 -> ratio 1.5 > 1.2 upper rail, >15yrs left -> cut 10%
    new = spending.guardrails(prev=100_000, portfolio=1_000_000, iwr=0.04, params=p, years_remaining=25)
    assert new == pytest.approx(90_000)


def test_guardrails_raises_when_lower_rail_breached(cfg):
    p = cfg.spending_strategies["guardrails"]
    # CWR = 0.03, IWR = 0.04 -> ratio 0.75 < 0.80 lower rail -> raise 10%
    new = spending.guardrails(prev=100_000, portfolio=3_333_333, iwr=0.04, params=p, years_remaining=25)
    assert new == pytest.approx(110_000)
