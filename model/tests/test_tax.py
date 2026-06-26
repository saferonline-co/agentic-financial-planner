"""TDD: Australian tax engine — brackets, Medicare, super, CGT, reconciliation."""
import pytest
from finmodel import schema, tax


@pytest.fixture
def cfg():
    return schema.load_config()


def test_income_tax_brackets(cfg):
    # 2024-25 resident scale, no Medicare.
    assert tax.income_tax(18200, cfg) == pytest.approx(0.0)
    assert tax.income_tax(45000, cfg) == pytest.approx(4288.0)         # 26800*0.16
    assert tax.income_tax(135000, cfg) == pytest.approx(4288 + 27000)  # +90000*0.30
    # 345k: 4288 + 27000 + 55000*0.37 + 155000*0.45
    assert tax.income_tax(345000, cfg) == pytest.approx(121388.0)


def test_medicare_levy(cfg):
    assert tax.medicare(345000, cfg) == pytest.approx(6900.0)  # 2%


def test_total_income_tax_includes_medicare(cfg):
    assert tax.total_income_tax(345000, cfg) == pytest.approx(121388 + 6900)


def test_take_home_reconciles(cfg):
    # Person 1: 380k gross, 35k concessional (salary sacrifice) -> taxable 345k.
    # Stated take-home ~210k. Engine should land within a sensible band.
    th = tax.take_home(gross=380_000, concessional=35_000, cfg=cfg)
    assert th == pytest.approx(210_000, abs=12_000)


def test_super_contributions_tax_div293_for_high_earner(cfg):
    # Person 1 income > 250k -> 15% + 15% Div293 = 30%.
    assert tax.super_contributions_tax(35_000, income=380_000, cfg=cfg) == pytest.approx(10_500)
    # Person 2 income < 250k -> 15% only.
    assert tax.super_contributions_tax(17_000, income=140_000, cfg=cfg) == pytest.approx(2_550)


def test_cgt_on_drawdown_uses_discount(cfg):
    # Realise a gain with 50% discount, taxed at a marginal rate.
    # withdraw 100k from a parcel with 60% gain fraction -> gain 60k -> taxable 30k.
    t = tax.cgt_on_withdrawal(withdrawal=100_000, gain_fraction=0.60, marginal_rate=0.30, cfg=cfg)
    assert t == pytest.approx(30_000 * 0.30)


def test_investment_income_tax_marginal_and_franking(cfg):
    yields = {"equity": 0.03, "bond": 0.04, "cash": 0.04}
    alloc = {"equity": 0.9, "bond": 0.1}
    # $500k cash interest ($20k): Person 1 at top marginal, Person 2 at $0 (tax-free threshold).
    net, _ = tax.investment_income_tax(500_000, 0, alloc, yields, {"person1": 345_000, "person2": 0}, cfg)
    assert net == pytest.approx(4_900, abs=700)
    # Franking softens dividends: low-income retirees pay well below full marginal.
    net2, _ = tax.investment_income_tax(0, 1_000_000, alloc, yields,
                                        {"person1": 15_000, "person2": 15_000}, cfg)
    full_marginal_on_divs = 1_000_000 * 0.9 * 0.03 * 0.30
    assert net2 < full_marginal_on_divs
    # etf_income returned = the reinvested distribution (lifts cost base).
    _, ei = tax.investment_income_tax(0, 1_000_000, alloc, yields, {"person1": 0, "person2": 0}, cfg)
    assert ei == pytest.approx(1_000_000 * (0.9 * 0.03 + 0.1 * 0.04))


def test_super_earnings_rate_phase_dependent(cfg):
    assert tax.super_earnings_rate("accumulation", cfg) == pytest.approx(0.15)
    assert tax.super_earnings_rate("pension", cfg) == pytest.approx(0.0)


# ---- proposed 2027 CGT regime (50% discount removed + 30% floor) ----

def _cfg_2027():
    cfg = schema.load_config()
    cfg.tax["cgt"]["enabled_2027"] = True
    return cfg


def test_cgt_2027_regime_exceeds_discount():
    cfg = _cfg_2027()
    args = dict(withdrawal=100_000, gain_fraction=0.60, marginal_rate=0.45)
    discount = tax.cgt_on_withdrawal(**args, cfg=schema.load_config(), year=2030)
    regime = tax.cgt_on_withdrawal(**args, cfg=cfg, year=2030)
    # high marginal: 60k gain * 0.45 (no discount) vs 60k*0.5*0.45 with discount.
    assert regime == pytest.approx(60_000 * 0.45)
    assert regime > discount


def test_cgt_2027_floor_binds_at_low_marginal():
    cfg = _cfg_2027()
    # low marginal (20%) -> the 30% floor binds: 60k gain * 0.30.
    t = tax.cgt_on_withdrawal(100_000, 0.60, marginal_rate=0.20, cfg=cfg, year=2030)
    assert t == pytest.approx(60_000 * 0.30)


def test_cgt_2027_inactive_before_change_year():
    cfg = _cfg_2027()
    # 2026 < change_year 2027 -> falls back to the discount method.
    t = tax.cgt_on_withdrawal(100_000, 0.60, marginal_rate=0.30, cfg=cfg, year=2026)
    assert t == pytest.approx(30_000 * 0.30)


def test_cgt_default_year_none_uses_discount(cfg):
    # Backward compatibility: no year passed -> discount regime regardless.
    cfg.tax["cgt"]["enabled_2027"] = True
    t = tax.cgt_on_withdrawal(100_000, 0.60, marginal_rate=0.30, cfg=cfg)
    assert t == pytest.approx(30_000 * 0.30)
