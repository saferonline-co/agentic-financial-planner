"""TDD: engine order-of-operations, events, drawdown, net worth, depletion."""
import pytest
from finmodel import schema, engine, returns
from finmodel.returns import DeterministicReturns


@pytest.fixture
def cfg():
    return schema.load_config()


@pytest.fixture
def det(cfg):
    return DeterministicReturns(cfg, band="central")


def run(cfg, det, **kw):
    return engine.run(cfg, det, **kw)


def test_produces_a_row_per_year(cfg, det):
    rows = run(cfg, det)
    assert rows[0].year == 2026
    assert rows[-1].year == 2072
    assert len(rows) == 2072 - 2026 + 1


def test_opening_net_worth_reconciles_in_first_year(cfg, det):
    rows = run(cfg, det)
    # Year 1: after the foreign-property sale and growth; NW should be close to the
    # opening figure plus first-year growth/savings — sanity bounds.
    assert 1_400_000 < rows[0].net_worth_nominal < 1_800_000


def test_foreign_property_sale_moves_to_cash(cfg, det):
    rows = run(cfg, det)
    # foreign_property account is zero from 2026 onward
    assert rows[0].accounts["foreign_property"] == 0.0


def test_accumulation_grows_net_worth(cfg, det):
    rows = run(cfg, det)
    nw2026 = rows[0].net_worth_today
    nw2035 = next(r for r in rows if r.year == 2035).net_worth_today
    assert nw2035 > nw2026


def test_house_purchase_creates_house_and_mortgage(cfg, det):
    rows = run(cfg, det)
    pre = next(r for r in rows if r.year == 2030)
    post = next(r for r in rows if r.year == 2031)
    assert pre.house_value == 0
    # Bought 2031 at the schedule-implied market price, and BELOW a bullish
    # 5%-escalation entry (the schedule grows slower than 5%/yr nominal).
    price = cfg.house["target_price_today"]
    assert post.house_value == pytest.approx(price * returns.house_growth_factor(cfg, 2031))
    assert post.house_value < price * 1.05 ** 5
    assert post.mortgage > 0


def test_house_paid_off_by_retirement(cfg, det):
    rows = run(cfg, det)
    r2040 = next(r for r in rows if r.year == 2040)   # Person 1 retires 2040
    assert r2040.mortgage == pytest.approx(0.0, abs=1.0)


def test_inheritance_injected_at_2036(cfg, det):
    rows = run(cfg, det)
    r = next(r for r in rows if r.year == 2036)
    # full variant 600k grown by inflation to 2036
    assert r.inheritance > 600_000


def test_inheritance_variant_zero(cfg, det):
    rows = run(cfg, det, inheritance_variant="zero")
    r = next(r for r in rows if r.year == 2036)
    assert r.inheritance == 0.0


def test_person1_super_not_drawn_while_working(cfg, det):
    # Person 1's super is locked until its access_year (2040, preservation age 60 =
    # retirement). It must not be drawn while still working, so it keeps growing
    # through the final working years despite a drawdown stress.
    rows = run(cfg, det, inheritance_variant="zero", spending_strategy="constant_real")
    r2036 = next(r for r in rows if r.year == 2036)
    r2037 = next(r for r in rows if r.year == 2037)
    assert r2037.accounts["person1_super"] >= r2036.accounts["person1_super"]


def test_retirement_spend_follows_glidepath(cfg, det):
    rows = run(cfg, det)
    # First retired year is 2040 (Person 1 retires 2040). Spend pegs to the OLDER
    # partner (Person 2, b.1968), who is past the age-70 flat, so retirement opens
    # on the declining leg, below the 120k base, and falls to the 0.75x floor (90k).
    r2041 = next(r for r in rows if r.year == 2041)
    r2060 = next(r for r in rows if r.year == 2060)
    need2041_real = r2041.need / r2041.infl
    need2060_real = r2060.need / r2060.infl
    assert 99_000 < need2041_real < 120_000       # declining leg, not the flat base
    assert need2060_real < need2041_real          # smile decline continues
    assert need2060_real == pytest.approx(90_000, abs=2_000)  # floor 0.75


def test_today_money_is_nominal_deflated(cfg, det):
    rows = run(cfg, det)
    r = next(r for r in rows if r.year == 2046)  # n=20
    assert r.net_worth_today == pytest.approx(r.net_worth_nominal / r.infl)


def test_depletion_breaks_the_run(cfg, det):
    # Absurd spend to force depletion before horizon.
    cfg.raw["retirement_spending"]["base"] = 600_000
    rows = run(cfg, det, inheritance_variant="zero", spending_strategy="constant_real")
    assert rows[-1].depleted
    assert rows[-1].year < 2072
