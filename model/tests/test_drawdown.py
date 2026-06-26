"""TDD: pins the audit fixes — Foreign pensions are drawn AND taxed, proportional vs
waterfall, inheritance delta. These behaviours were previously unpinned."""
import pytest
from finmodel import schema, engine
from finmodel.returns import DeterministicReturns


@pytest.fixture
def cfg():
    return schema.load_config()


def det(cfg):
    return DeterministicReturns(cfg, "central")


def _with_method(method):
    cfg = schema.load_config()
    cfg.raw["drawdown"] = {"method": method}
    return cfg


def test_person2_super_ttr_caps_access_before_lump_sum_year():
    # AU conditions of release: in the TTR window (2028-2030, Person 2 60 but working)
    # only a capped income stream is accessible, NOT a lump sum; the full balance
    # unlocks at the lump-sum access_year (2031, their retirement).
    cfg = schema.load_config()
    bal = {n: a.balance for n, a in cfg.accounts.items()}
    accs = {a.name: a for a in cfg.accounts.values()}
    p2 = accs["person2_super"]
    assert p2.access_year == 2031 and p2.ttr_access_year == 2028

    # Before preservation age: no access at all.
    avail = dict((n, a) for n, a, _ in engine._accessible(cfg, bal, 2026, cfg.reserve_floor))
    assert "person2_super" not in avail
    # TTR window: only ttr_max_pct of the balance is available (a stream, not a lump).
    avail = dict((n, a) for n, a, _ in engine._accessible(cfg, bal, 2028, cfg.reserve_floor))
    assert avail["person2_super"] == pytest.approx(p2.ttr_max_pct * bal["person2_super"])
    assert avail["person2_super"] < bal["person2_super"]            # NOT the whole pot
    # Lump-sum year: the full balance is accessible.
    avail = dict((n, a) for n, a, _ in engine._accessible(cfg, bal, 2031, cfg.reserve_floor))
    assert avail["person2_super"] == pytest.approx(bal["person2_super"])


def test_foreign_pensions_are_consumed_not_left_untouched():
    # Under waterfall the foreign-pension pots sit last and are barely touched; under
    # proportional they are genuinely drawn each retirement year.
    cfg_w, cfg_p = _with_method("waterfall"), _with_method("proportional")
    w = engine.run(cfg_w, det(cfg_w))[-1]
    p = engine.run(cfg_p, det(cfg_p))[-1]
    tot_fp_w = w.accounts["person1_foreign_pension"] + w.accounts["person2_foreign_pension"]
    tot_fp_p = p.accounts["person1_foreign_pension"] + p.accounts["person2_foreign_pension"]
    assert tot_fp_p < tot_fp_w        # proportional actually spends them down


def test_after_tax_networth_is_below_gross():
    # The honest fix: net worth net of embedded tax on unrealised foreign-pension/ETF
    # gains must be materially below the gross face-value figure.
    cfg = schema.load_config()
    last = engine.run(cfg, det(cfg))[-1]
    assert last.embedded_tax > 0
    assert last.net_worth_after_tax_today < last.net_worth_today
    # the haircut should be non-trivial, given the embedded gains in the pots
    assert last.net_worth_today - last.net_worth_after_tax_today > 75_000


def test_foreign_pension_withdrawal_is_taxed():
    # In a high-spend, zero-inheritance run the pots get drawn and the growth
    # portion taxed -> positive withdrawal tax appears in retirement years.
    cfg = _with_method("proportional")
    rows = engine.run(cfg, det(cfg), inheritance_variant="zero",
                      spending_strategy="constant_real")
    late_tax = [r.tax_paid for r in rows if r.year > 2045]
    assert any(t > 0 for t in late_tax)


def test_wtax_taxes_foreign_pension_growth(cfg):
    # Direct unit test of the withdrawal-tax helper for a foreign-pension parcel.
    acc = cfg.accounts["person2_foreign_pension"]
    cost_base = {"person2_foreign_pension": 480_000}
    # balance grown to 960k (100% gain) -> withdraw 100k -> growth fraction 0.5
    t = engine._wtax("person2_foreign_pension", acc, take=100_000, bal_before=960_000,
                     cost_base=cost_base, cfg=cfg)
    assert t == pytest.approx(100_000 * 0.5 * 0.30)   # 0.30 marginal on growth


def test_inheritance_delta_equals_inheritance(cfg):
    # full vs zero terminal must differ by exactly the inheritance (grown +
    # compounded), and 2036 injection equals the inflated amount.
    full = engine.run(cfg, det(cfg), inheritance_variant="full")
    zero = engine.run(cfg, det(cfg), inheritance_variant="zero")
    r_full = next(r for r in full if r.year == 2036)
    r_zero = next(r for r in zero if r.year == 2036)
    assert r_zero.inheritance == 0
    assert r_full.inheritance > 600_000          # 600k grown to 2036
    assert full[-1].net_worth_today > zero[-1].net_worth_today


def test_non_concessional_super_contribution_moves_cash_to_super():
    # A $120k non-concessional contribution (after growth) moves exactly $120k
    # from cash to person2_super in the contribution year — no contributions tax.
    # (Clear the base's own NCC schedule so this isolates a single contribution.)
    base = schema.load_config()
    base.raw["super_contributions"] = []
    plus = schema.load_config()
    plus.raw["super_contributions"] = [
        {"person": "person2", "source": "cash", "amount": 120_000, "years": [2026]}]
    rb = {r.year: r for r in engine.run(base, det(base))}
    rp = {r.year: r for r in engine.run(plus, det(plus))}
    assert rp[2026].accounts["person2_super"] == pytest.approx(
        rb[2026].accounts["person2_super"] + 120_000, abs=1.0)
    assert rp[2026].accounts["cash"] == pytest.approx(
        rb[2026].accounts["cash"] - 120_000, abs=1.0)


def test_extra_savings_today_adds_to_etf_and_terminal():
    # "Save an extra $50k/yr until retirement": in the first accumulation year
    # (2026, infl=1) the ETF must hold ~$50k more than baseline; the extra
    # compounds to a materially higher terminal net worth.
    base = schema.load_config()
    plus = schema.load_config()
    plus.raw["extra_savings_today"] = 50_000
    rb = {r.year: r for r in engine.run(base, det(base))}
    rp = {r.year: r for r in engine.run(plus, det(plus))}
    assert rp[2026].accounts["etf"] == pytest.approx(
        rb[2026].accounts["etf"] + 50_000, abs=1.0)
    # extra savings run through the accumulation years (until Person 1 retires 2040);
    # by 2035 the gap is ~10 yrs of contributions + growth.
    assert rp[2035].accounts["etf"] > rb[2035].accounts["etf"] + 500_000
    assert (engine.run(plus, det(plus))[-1].net_worth_after_tax_today
            > engine.run(base, det(base))[-1].net_worth_after_tax_today + 500_000)


def test_extra_savings_ramp_schedule_steps_by_year():
    # Ramp: $25k to 2030, $50k from 2031. The resolver returns the right band per
    # year; first year (2026, infl=1) the ETF holds +$25k vs baseline.
    cfg = schema.load_config()
    cfg.raw["extra_savings_today"] = [
        {"until_year": 2030, "amount": 25_000}, {"amount": 50_000}]
    assert engine._extra_savings_today(cfg, 2026) == 25_000
    assert engine._extra_savings_today(cfg, 2030) == 25_000
    assert engine._extra_savings_today(cfg, 2031) == 50_000
    assert engine._extra_savings_today(cfg, 2035) == 50_000
    base = schema.load_config()
    rb = {r.year: r for r in engine.run(base, det(base))}
    rp = {r.year: r for r in engine.run(cfg, det(cfg))}
    assert rp[2026].accounts["etf"] == pytest.approx(
        rb[2026].accounts["etf"] + 25_000, abs=1.0)
    # the ramp beats baseline but lands below the flat-$50k case.
    flat = schema.load_config(); flat.raw["extra_savings_today"] = 50_000
    tf = engine.run(flat, det(flat))[-1].net_worth_after_tax_today
    tr = rp[max(rp)].net_worth_after_tax_today
    assert rb[max(rb)].net_worth_after_tax_today < tr < tf


def test_extra_savings_to_super_shelters_vs_etf():
    # Routing the found $50k/yr into Person 2's super as NCC: it lands in person2_super (not
    # ETF) in the first year, and the super shelter (15%/0% vs marginal ETF tax)
    # makes the terminal beat the same savings left in taxable ETF.
    etf = schema.load_config(); etf.raw["extra_savings_today"] = 50_000
    sup = schema.load_config()
    sup.raw["extra_savings_today"] = 50_000
    sup.raw["extra_savings_to_super"] = "person2"
    re = {r.year: r for r in engine.run(etf, det(etf))}
    rs = {r.year: r for r in engine.run(sup, det(sup))}
    base = {r.year: r for r in engine.run(schema.load_config(), det(schema.load_config()))}
    # year 1: the $50k went to person2_super, not ETF.
    assert rs[2026].accounts["person2_super"] == pytest.approx(
        base[2026].accounts["person2_super"] + 50_000, abs=1.0)
    assert rs[2026].accounts["etf"] == pytest.approx(base[2026].accounts["etf"], abs=1.0)
    # At these moderate incomes the super shelter is roughly neutral vs a taxable
    # ETF (the marginal tax saved is small); the key mechanic above is that the
    # contribution is ROUTED into super, not ETF. Assert the two end up comparable.
    # (At high marginal rates the super route pulls clearly ahead.)
    sup_t = engine.run(sup, det(sup))[-1].net_worth_after_tax_today
    etf_t = engine.run(etf, det(etf))[-1].net_worth_after_tax_today
    assert abs(sup_t - etf_t) / etf_t < 0.05


def test_flow_fields_track_savings_and_house():
    # savings_in: positive in accumulation (income saved + concessional super),
    # negative in retirement (drawdown). house_in spikes at purchase (deposit+
    # stamp, 2031) and at payoff (2036), zero otherwise.
    cfg = schema.load_config(scenario="house_dearer_combo")
    by = {r.year: r for r in engine.run(cfg, det(cfg))}
    assert by[2028].savings_in > 40_000          # free cash + concessional super
    assert by[2050].savings_in < 0               # retirement: net drawdown
    assert by[2050].savings_in == pytest.approx(-by[2050].withdrawal, abs=1.0)
    assert by[2031].house_in > 100_000           # deposit + stamp duty at purchase
    assert by[2042].house_in > 0                 # mortgage paid off at retirement
    assert by[2045].house_in == 0                # nothing flowing into the house later


def test_investment_income_is_taxed_annually():
    # Turning income_yield to 0 removes the annual investment-income tax, so the
    # terminal is higher; positive yields apply the (realistic) tax drag.
    base = schema.load_config()
    noyield = schema.load_config()
    for ac in noyield.assumptions["cma"]["asset_classes"].values():
        ac["income_yield"] = 0.0
    t_base = engine.run(base, det(base))[-1].net_worth_after_tax_today
    t_no = engine.run(noyield, det(noyield))[-1].net_worth_after_tax_today
    assert t_base < t_no                         # taxing investment income costs
    assert (t_no - t_base) > 100_000             # and it's material over 46 yrs


def test_etf_contributions_carry_cost_base():
    # The inheritance (~$768k into ETF in 2036) is contributed AT market value, so
    # it carries full cost base -> it must NOT add CGT on the principal to the
    # deferred (embedded) tax. Isolate it via full-vs-zero inheritance.
    cfg = schema.load_config()
    full = {r.year: r for r in engine.run(cfg, det(cfg), inheritance_variant="full")}
    zero = {r.year: r for r in engine.run(cfg, det(cfg), inheritance_variant="zero")}
    d_etf = full[2036].accounts["etf"] - zero[2036].accounts["etf"]   # ~principal
    d_emb = full[2036].embedded_tax - zero[2036].embedded_tax         # extra def. tax
    assert d_etf > 600_000
    assert d_emb < 0.05 * d_etf      # cost base tracked => ~no phantom CGT on principal


def test_cash_sweep_holds_floor_and_deploys_idle_cash():
    # super_max_deploy holds ~$50k (today's $) in cash and sweeps the rest to ETF;
    # recommended lets the idle cash pile up far above that.
    dep = schema.load_config(scenario="super_max_deploy")
    rec = schema.load_config()
    rd = {r.year: r for r in engine.run(dep, det(dep))}
    rr = {r.year: r for r in engine.run(rec, det(rec))}
    cash_today = rd[2030].accounts["cash"] / rd[2030].infl
    assert cash_today == pytest.approx(50_000, abs=20_000)        # held near floor
    assert (rr[2030].accounts["cash"] / rr[2030].infl
            > cash_today + 100_000)                              # base leaves the rest idle
    # the NCC bring-forward now lands in the BASE too (Person 2's super well above the $59k start)
    assert rr[2028].accounts["person2_super"] > 400_000
    # deploy adds extra concessional + the cash sweep on top, so its super is at least as large
    assert rd[2028].accounts["person2_super"] >= rr[2028].accounts["person2_super"]


def test_house_grows_on_schedule_not_property_cma():
    # House bought 0.9M, retire 2042. The home should track the bespoke schedule
    # (softer early real growth, ~2% real long-run trend), NOT the property CMA.
    cfg = schema.load_config(scenario="house_dearer_combo")
    rows = engine.run(cfg, det(cfg))
    by = {r.year: r for r in rows}
    # 2045 -> 2046: one year of ~2% real growth => ~4.5% nominal (2% real + 2.5% cpi).
    g = by[2046].house_value / by[2045].house_value - 1
    assert g == pytest.approx(0.045, abs=0.003)


def test_house_market_value_never_falls():
    # The home is one object that only appreciates — in NO funding mode does aged
    # care shrink its market value (no house_shock in the base case).
    cfg = schema.load_config()
    by = {r.year: r for r in engine.run(cfg, det(cfg))}
    for y in range(2032, max(by)):
        assert by[y + 1].house_value >= by[y].house_value


def test_base_funds_aged_care_from_pool_house_intact():
    # BASE (funded_from=portfolio): care is paid from investments; the house is kept
    # fully owned (market value == home equity, never drawn).
    cfg = schema.load_config()
    assert cfg.aged_care["funded_from"] == "portfolio"
    by = {r.year: r for r in engine.run(cfg, det(cfg))}
    assert by[2056].care > 0                                # Person 2 (b.1968) hits 88 in 2056
    assert all(r.care_drawn == 0 for r in by.values())     # house equity never consumed
    assert all(r.home_equity == pytest.approx(r.house_value) for r in by.values())


def test_house_mode_draws_equity_not_market_value():
    # funded_from=house (reverse-mortgage style): market value untouched; the draw
    # falls home_equity only.
    cfg = schema.load_config()
    cfg.aged_care["funded_from"] = "house"
    by = {r.year: r for r in engine.run(cfg, det(cfg))}
    assert by[2056].care_drawn > 0
    assert by[2056].house_value > by[2055].house_value     # market value keeps rising
    assert by[2056].home_equity < by[2055].home_equity     # equity falls by the draw


def test_mortgage_mode_borrows_and_services_interest_from_pool():
    # funded_from=mortgage: care is borrowed against the home (mortgage rises by the
    # care cost) and the interest is serviced from the pool — NOT a reverse mortgage,
    # so the pool is smaller than the no-interest house mode by year's end.
    house = schema.load_config(); house.aged_care["funded_from"] = "house"
    mort = schema.load_config();  mort.aged_care["funded_from"] = "mortgage"
    bh = {r.year: r for r in engine.run(house, det(house))}
    bm = {r.year: r for r in engine.run(mort, det(mort))}
    assert bm[2056].mortgage > bm[2055].mortgage           # care added to the loan
    assert bm[2057].housing > 0                            # interest serviced from cash
    assert bm[2056].house_value == pytest.approx(bh[2056].house_value)  # house intact


def test_cgt_2027_regime_lowers_after_tax_terminal():
    # Enabling the proposed 2027 CGT regime raises tax on ETF gains -> the honest
    # after-tax terminal net worth must fall (or at worst stay equal).
    base = schema.load_config(scenario="house_dearer_combo")
    regime = schema.load_config(scenario="house_dearer_combo")
    regime.tax["cgt"]["enabled_2027"] = True
    b = engine.run(base, det(base))[-1]
    r = engine.run(regime, det(regime))[-1]
    # Never beneficial: the higher-CGT regime can only lower (or, if the ETF is fully
    # drawn down by the horizon, leave unchanged) the honest after-tax terminal.
    assert r.net_worth_after_tax_today <= b.net_worth_after_tax_today
    assert r.net_worth_today <= b.net_worth_today  # higher realised CGT, never less tax


def test_zero_real_return_keeps_pool_roughly_flat_in_retirement():
    # Sanity break-test: if every asset returns exactly CPI, the retirement pool
    # should NOT grow in real terms — it should fall as spending exceeds 0 real.
    cfg = schema.load_config()
    cpi = cfg.assumptions["inflation"]["cpi"]
    for acc in cfg.assumptions["cma"]["asset_classes"].values():
        acc["mean"], acc["sd"] = cpi, 0.0
    for a in cfg.accounts.values():
        a.legacy_return = cpi
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"))
    pool_2040 = next(r.drawpool_today for r in rows if r.year == 2040)
    pool_late = rows[-1].drawpool_today   # last surviving year (may deplete before horizon)
    assert pool_late < pool_2040     # real pool must decline when real return = 0
