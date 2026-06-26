"""The forward-simulation engine — canonical annual order-of-operations.

Per year: open balances -> index for inflation -> recognise gross income ->
expenses & debt -> tax -> net cash -> allocate (surplus to savings / shortfall
to a drawdown waterfall that respects super access) -> apply growth -> close.

Deterministic vs Monte Carlo differ only by the injected ReturnsProvider. No I/O,
no randomness here. Compute nominal; report today's money = nominal / (1+cpi)^n.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import tax
from .events import phase_for_year, resolve_events, retirement_year
from .returns import ReturnsProvider, house_growth_factor
from .schema import Account, Config

# Tax-efficient drawdown order; access_year gate + reserve floor applied in draw().
DECUM_ORDER = ["cash", "etf", "person2_super", "person1_super", "person2_foreign_pension", "person1_foreign_pension", "person1_taxfree"]


@dataclass
class YearRow:
    year: int
    person1_age: int
    person2_age: int
    older_age: int
    phase: str
    infl: float
    gross_income: float = 0.0
    take_home: float = 0.0
    pension_income: float = 0.0
    inheritance: float = 0.0
    living: float = 0.0
    housing: float = 0.0          # rent or mortgage interest
    school: float = 0.0
    ip_carry: float = 0.0
    care: float = 0.0
    tax_paid: float = 0.0
    need: float = 0.0             # retirement spend target (nominal)
    withdrawal: float = 0.0       # drawn from portfolio to fund need
    net_cashflow: float = 0.0
    savings_in: float = 0.0        # net new money into the investible pool (income
                                   # saved + concessional super); -withdrawal in retirement
    house_in: float = 0.0          # cash directed into the home (deposit+stamp, payoff)
    accounts: dict[str, float] = field(default_factory=dict)
    house_value: float = 0.0       # home MARKET value (nominal) — never reduced by aged care
    care_drawn: float = 0.0        # cumulative aged-care paid from home equity (nominal)
    home_equity: float = 0.0       # house_value - care_drawn, floored at 0 (nominal)
    mortgage: float = 0.0
    drawpool: float = 0.0
    drawpool_today: float = 0.0    # investible pool ex-house, today's money
    net_worth_nominal: float = 0.0
    net_worth_today: float = 0.0
    embedded_tax: float = 0.0      # tax owed if unrealised gains were realised
    net_worth_after_tax_today: float = 0.0  # the honest spendable/bequeathable figure
    depleted: bool = False


def _extra_savings_today(cfg: Config, year: int) -> float:
    """Resolve the extra-savings lever for a year. Accepts a flat number, or an
    ordered list of {until_year, amount} regimes (last entry open-ended) for a
    ramp — e.g. $25k to 2030 then $50k. Today's money (caller inflates)."""
    spec = cfg.raw.get("extra_savings_today", 0.0)
    if isinstance(spec, (int, float)):
        return float(spec)
    for regime in spec:
        if "until_year" not in regime or year <= regime["until_year"]:
            return float(regime["amount"])
    return 0.0


def _house_account(cfg: Config) -> Account:
    legacy = cfg.assumptions["cma"]["asset_classes"]["property"]
    geo = legacy["mean"] - 0.5 * legacy["sd"] ** 2
    return Account("house", "property", 0.0, "joint", cfg.start_year, {"property": 1.0}, legacy_return=geo)


def _wtax(name: str, acc: Account, take: float, bal_before: float,
         cost_base: dict[str, float], cfg: Config, year: int | None = None) -> float:
    """Tax on realising `take` from an account: CGT (discount or 2027 regime) on a
    taxable parcel, marginal income tax on the growth portion of a foreign-pension
    withdrawal (assessable foreign income). Updates the cost base. Tax-free
    wrappers -> 0. `year` selects the CGT regime (2027 change is year-gated)."""
    if take <= 0 or bal_before <= 0:
        return 0.0
    cb = cost_base.get(name, bal_before)
    gain_fraction = max(0.0, (bal_before - cb) / bal_before)
    t = 0.0
    if acc.wrapper == "taxable":
        t = tax.cgt_on_withdrawal(take, gain_fraction, marginal_rate=0.30, cfg=cfg, year=year)
    elif acc.wrapper == "foreign_pension" and cfg.tax.get("foreign_pension_assessable"):
        rate = cfg.tax.get("foreign_pension_withdrawal_rate", 0.30)
        t = take * gain_fraction * rate
    cost_base[name] = cb * (1 - take / bal_before)
    return t


def _accessible(cfg: Config, bal: dict[str, float], year: int, reserve: float):
    """(name, available, account) for each accessible non-house pot.

    Respects the cash reserve floor, per-account `access_year` (full / lump-sum
    access, i.e. a condition of release met), and an optional Transition-to-
    Retirement window: from `ttr_access_year` (preservation age 60 while still
    working) a super pot yields ONLY a capped income stream (`ttr_max_pct` of the
    balance per year), not a lump sum, until `access_year` unlocks the full
    balance. Mirrors AU super conditions of release (e.g. Person 2: TTR from 2027,
    lump sum on her 2031 retirement)."""
    accts = {a.name: a for a in cfg.accounts.values()}
    out = []
    for name in DECUM_ORDER:
        if name not in bal:
            continue
        acc = accts[name]
        floor = reserve if name == "cash" else 0.0
        if year >= acc.access_year:
            avail = max(0.0, bal[name] - floor)                 # full / lump-sum
        elif acc.ttr_access_year is not None and year >= acc.ttr_access_year:
            avail = max(0.0, acc.ttr_max_pct * bal[name])       # capped TTR stream
        else:
            continue
        if avail > 0:
            out.append((name, avail, acc))
    return out


def _draw(bal: dict[str, float], amount: float, year: int, cfg: Config,
          reserve: float, cost_base: dict[str, float]) -> tuple[float, float]:
    """Tax-efficient waterfall draw (cash -> etf -> super -> pensions). Returns
    (shortfall, withdrawal_tax)."""
    remaining = amount
    wtax = 0.0
    for name, avail, acc in _accessible(cfg, bal, year, reserve):
        if remaining <= 0:
            break
        take = min(avail, remaining)
        wtax += _wtax(name, acc, take, bal[name], cost_base, cfg, year)
        bal[name] -= take
        remaining -= take
    return remaining, wtax


def _draw_proportional(bal: dict[str, float], amount: float, year: int, cfg: Config,
                       reserve: float, cost_base: dict[str, float]) -> tuple[float, float]:
    """Draw `amount` pro-rata across all accessible pots (so the largest pots are
    genuinely consumed and taxed, not left untouched). Returns (shortfall, tax)."""
    pots = _accessible(cfg, bal, year, reserve)
    total = sum(a for _, a, _ in pots)
    if total <= 0:
        return amount, 0.0
    wtax = 0.0
    scale = min(1.0, amount / total)
    for name, avail, acc in pots:
        take = avail * scale
        wtax += _wtax(name, acc, take, bal[name], cost_base, cfg, year)
        bal[name] -= take
    return max(0.0, amount - total), wtax


def _embedded_tax(bal: dict[str, float], cost_base: dict[str, float], cfg: Config,
                  year: int | None = None) -> float:
    """Deferred tax owed if unrealised gains were realised: CGT (discount or 2027
    regime) on taxable parcels, marginal on foreign-pension growth (AFE). Super (pension
    phase) and tax-free wrappers incur no withdrawal tax -> nil. Makes reported net worth
    after-tax/honest. `year` selects the CGT regime."""
    accts = {a.name: a for a in cfg.accounts.values()}
    t = 0.0
    for name, b in bal.items():
        acc = accts.get(name)
        if acc is None or b <= 0:
            continue
        gain = max(0.0, b - cost_base.get(name, b))
        if acc.wrapper == "taxable":
            t += tax.cgt_on_withdrawal(b, gain / b, marginal_rate=0.30, cfg=cfg, year=year)
        elif acc.wrapper == "foreign_pension" and cfg.tax.get("foreign_pension_assessable"):
            t += gain * cfg.tax.get("foreign_pension_withdrawal_rate", 0.30)
    return t


def _draw_need(bal: dict[str, float], amount: float, year: int, cfg: Config,
               reserve: float, cost_base: dict[str, float]) -> tuple[float, float]:
    """Retirement-need draw, dispatched by config drawdown.method."""
    method = cfg.raw.get("drawdown", {}).get("method", "waterfall")
    if method == "proportional":
        return _draw_proportional(bal, amount, year, cfg, reserve, cost_base)
    return _draw(bal, amount, year, cfg, reserve, cost_base)


def _pension_income(cfg: Config, year: int, infl: float) -> float:
    total = 0.0
    for person in ("person2", "person1"):
        p = cfg.pensions[person]
        if year >= p["start_year"]:
            total += p["amount_today"] * (infl if p["indexed"] else 1.0)
    return total


def run(cfg: Config, provider: ReturnsProvider, *,
        legacy: bool = False, inheritance_variant: str | None = None,
        spending_strategy: str | None = None) -> list[YearRow]:
    from . import spending as spend_mod

    ev = resolve_events(cfg)
    retire = retirement_year(cfg)
    start, horizon = cfg.start_year, cfg.horizon_year
    cpi = cfg.assumptions["inflation"]["cpi"]
    earn = cfg.assumptions["inflation"]["earnings"]
    care_infl = cfg.assumptions["inflation"]["care_cost"]
    older = cfg.older_partner
    rspend = cfg.raw["retirement_spending"]
    strategy = spending_strategy or rspend["strategy"]
    spend_base = rspend["base"]
    extra_rent = rspend.get("extra_rent_today", 0.0)
    inh_variant = inheritance_variant or cfg.inheritance["selected"]

    bal = {n: a.balance for n, a in cfg.accounts.items()}
    bal["cash"] += float(cfg.liabilities.get("tax_liability", 0.0))  # settle yr1
    cost_base = {n: (a.cost_base if a.cost_base is not None else a.balance)
                 for n, a in cfg.accounts.items()}
    house_acc = _house_account(cfg)
    house_value = 0.0          # home MARKET value (grows on its schedule; only a
                               # house_shock falls it — aged care does NOT touch it)
    care_drawn = 0.0           # cumulative aged-care paid out of home equity (nominal)
    mortgage = 0.0
    reserve = cfg.reserve_floor
    rows: list[YearRow] = []
    depleted = False
    prev_real_spend: float | None = None   # for path-dependent spending strategies
    iwr: float | None = None               # initial withdrawal rate (guardrails/vanguard)
    yields = {k: v.get("income_yield", 0.0)
              for k, v in cfg.assumptions["cma"]["asset_classes"].items()}
    etf_alloc = cfg.accounts["etf"].allocation

    for year in range(start, horizon + 1):
        n = year - start
        infl = (1 + cpi) ** n
        infl_earn = (1 + earn) ** n
        person1_age, person2_age = cfg.age("person1", year), cfg.age("person2", year)
        older_age = cfg.age(older, year)
        phase = phase_for_year(cfg, year)
        in_accum = year < retire
        row = YearRow(year, person1_age, person2_age, older_age, phase["name"], infl)
        open_cash, open_etf = bal.get("cash", 0.0), bal.get("etf", 0.0)  # for income tax

        # ---- events: foreign-property sale (before growth) ----
        if year == ev.get("foreign_property_sale") and bal.get("foreign_property"):
            bal["cash"] += cfg.accounts["foreign_property"].sale_value
            bal["foreign_property"] = 0.0

        # ---- growth (end-of-year convention: grow opening balances) ----
        for name, acc in cfg.accounts.items():
            if bal.get(name, 0) == 0:
                continue
            r = provider.account_rate(acc, year)
            if acc.wrapper == "super" and not legacy:
                phase_super = "accumulation" if in_accum else "pension"
                r *= (1 - tax.super_earnings_rate(phase_super, cfg))
            bal[name] *= (1 + r)
        if house_value:
            house_value *= (1 + provider.account_rate(house_acc, year))

        # ---- house purchase ----
        if cfg.house and year == ev.get("house_purchase"):
            # Market price at purchase = today's price x cumulative schedule growth.
            pp = cfg.house["target_price_today"] * house_growth_factor(cfg, year)
            dep = cfg.house["deposit_pct"] * pp
            stamp = cfg.house["stamp_duty_pct"] * pp + cfg.house["stamp_duty_fixed"]
            _draw(bal, dep + stamp, year, cfg, reserve, cost_base)
            house_value = pp
            mortgage = pp - dep
            row.house_in += dep + stamp

        # ---- inheritance ----
        if year == ev.get("inheritance"):
            amt = cfg.inheritance["variants"][inh_variant]
            if cfg.inheritance.get("grows_with_inflation"):
                amt *= infl
            bal["etf"] += amt
            cost_base["etf"] = cost_base.get("etf", 0.0) + amt   # inherited at market value
            row.inheritance = amt

        # ---- extra (non-concessional) super contributions ----
        # Move after-tax money from a source pot into a member's super in the
        # given years (e.g. bring-forward NCC, up to $120k/yr / $360k over 3yr).
        # Non-concessional => no contributions tax. Amount is nominal (the NCC
        # cap is a nominal $). Capped at the source balance (no overdraw).
        for sc in cfg.raw.get("super_contributions", []):
            if year in sc.get("years", []):
                src, dest = sc.get("source", "cash"), f"{sc['person']}_super"
                move = min(sc["amount"], bal.get(src, 0.0))
                bal[src] = bal.get(src, 0.0) - move
                bal[dest] = bal.get(dest, 0.0) + move

        # ---- annual tax on ongoing investment income (cash interest + ETF
        # distributions, franked on the AU-equity slice), at each person's marginal
        # rate. ETF distribution reinvested -> lifts cost base (no double-tax as CGT).
        # Funded below: reduces accumulation free-cash / adds to the retirement need.
        other_taxable = {}
        for person in ("person1", "person2"):
            t = 0.0
            if in_accum:
                pinc = phase.get("income", {}).get(person, {})
                g = (pinc.get("salary", 0) + pinc.get("bonus", 0)) * infl_earn
                c = cfg.raw.get("concessional_override", {}).get(
                    person, pinc.get("concessional_super", 0)) * infl_earn
                t += max(0.0, g - c)
            pp = cfg.pensions[person]
            if year >= pp["start_year"]:
                t += pp["amount_today"] * (infl if pp["indexed"] else 1.0)
            other_taxable[person] = t
        if legacy:
            inv_tax, etf_income = 0.0, 0.0
        else:
            inv_tax, etf_income = tax.investment_income_tax(
                open_cash, open_etf, etf_alloc, yields, other_taxable, cfg)
        cost_base["etf"] = cost_base.get("etf", 0.0) + etf_income

        # ---- income / expenses / tax / cashflow ----
        if in_accum:
            gross_total = take_home_total = tax_total = 0.0
            for person in ("person1", "person2"):
                inc = phase.get("income", {}).get(person, {})
                gross = (inc.get("salary", 0) + inc.get("bonus", 0)) * infl_earn
                # concessional_override (top-level, per person) lets a scenario max
                # the cap sparsely without rewriting the whole phases list.
                base_conc = cfg.raw.get("concessional_override", {}).get(
                    person, inc.get("concessional_super", 0))
                conc = base_conc * infl_earn
                if gross <= 0:
                    continue
                th = tax.take_home(gross, conc, cfg) if not legacy else (gross - conc) * 0.55
                # post-tax deductions consumed as benefits (HECS / insurance /
                # packaging): reduce cash available to save, not tax. Calibrates
                # take-home to canonical payslips => free cash ~$18k/yr (not ~$40k).
                od = inc.get("other_deductions", 0) * infl
                gross_total += gross
                take_home_total += th - od
                tax_total += (gross - conc) - th
                # contributions into super (net of contributions tax)
                ctax = 0.0 if legacy else tax.super_contributions_tax(conc, gross, cfg)
                bal[f"{person}_super"] += conc - ctax
                row.savings_in += conc - ctax        # income diverted into super
            exp = phase.get("expenses", {})
            living = exp.get("living", 0) * infl
            rent = exp.get("rent", 0) * infl
            if cfg.house is None and exp.get("rent", 0) == 0:
                rent = extra_rent * infl   # rent-forever: keep renting post-2031
            school = exp.get("school", 0) * infl
            ipc = exp.get("ip_carry", 0) * infl
            mort_interest = mortgage * cfg.house["mortgage_rate"] if mortgage else 0.0
            housing = rent + mort_interest
            outgoings = living + housing + school + ipc
            # extra_savings_today: a scenario lever for "find a way to save $X more
            # per year" (income found or expenses cut) until retirement. Today's
            # money; lands in ETF via free_cash. Applies only in accumulation years.
            # Either a flat number, or an ordered {until_year, amount} schedule
            # (last entry open-ended) for a ramp, e.g. $25k to 2030 then $50k.
            extra_savings = _extra_savings_today(cfg, year) * infl
            # extra_savings_to_super (person): route the found savings into that
            # person's super as a NON-CONCESSIONAL contribution (post-tax cash, no
            # 15% entry tax), capped at the NCC cap. Shelters the earnings at
            # 15%/0% vs the taxable ETF's annual marginal tax. Remainder -> ETF.
            to_super = cfg.raw.get("extra_savings_to_super")
            if to_super and extra_savings > 0:
                cap = cfg.tax["super"]["nonconcessional_cap"] * infl
                contrib = min(extra_savings, cap)
                bal[f"{to_super}_super"] += contrib
                row.savings_in += contrib            # extra savings sheltered in super
                extra_savings -= contrib
            free_cash = take_home_total - outgoings - inv_tax + extra_savings
            tax_total += inv_tax
            if free_cash >= 0:
                bal["etf"] += free_cash
                cost_base["etf"] = cost_base.get("etf", 0.0) + free_cash  # after-tax savings
            else:
                short, cgt = _draw(bal, -free_cash, year, cfg, reserve, cost_base)
                tax_total += cgt
            row.gross_income, row.take_home, row.tax_paid = gross_total, take_home_total, tax_total
            row.living, row.housing, row.school, row.ip_carry = living, housing, school, ipc
            row.net_cashflow = free_cash
            if free_cash > 0:
                row.savings_in += free_cash          # income saved into ETF

            # ---- cash sweep: deploy idle cash above a today's-money floor into
            # ETF. Reserve cash earmarked for not-yet-made NCC tranches so the
            # sweep and the bring-forward contributions don't starve each other. ----
            floor_today = cfg.raw.get("cash_sweep_floor_today")
            if floor_today is not None:
                reserved = sum(sc["amount"]
                               for sc in cfg.raw.get("super_contributions", [])
                               if sc.get("source", "cash") == "cash"
                               for y in sc.get("years", []) if y > year)
                excess = bal.get("cash", 0.0) - (floor_today * infl + reserved)
                if excess > 0:
                    bal["cash"] -= excess
                    bal["etf"] += excess
                    cost_base["etf"] = cost_base.get("etf", 0.0) + excess  # after-tax cash
        else:
            # ---- retirement: payoff, spend, draw ----
            if year == retire and mortgage > 0 and cfg.house["payoff_at_retirement"] == "full":
                _draw(bal, mortgage, year, cfg, reserve, cost_base)
                row.house_in += mortgage             # cash converting debt -> equity
                mortgage = 0.0
            pool_today_now = sum(bal.values()) / infl
            if strategy in ("blanchett_smile", "constant_real"):
                spend_real = spend_mod.real_spend(strategy, cfg, base=spend_base, older_age=older_age)
            elif strategy == "guardrails":
                if prev_real_spend is None:
                    spend_real, iwr = spend_base, spend_base / max(pool_today_now, 1.0)
                else:
                    spend_real = spend_mod.guardrails(
                        prev=prev_real_spend, portfolio=max(pool_today_now, 1.0), iwr=iwr,
                        params=cfg.spending_strategies["guardrails"], years_remaining=horizon - year)
            elif strategy == "vanguard_dynamic":
                if prev_real_spend is None:
                    spend_real, iwr = spend_base, spend_base / max(pool_today_now, 1.0)
                else:
                    spend_real = spend_mod.vanguard_dynamic(
                        prev=prev_real_spend, portfolio=max(pool_today_now, 1.0), wr=iwr,
                        params=cfg.spending_strategies["vanguard_dynamic"])
            else:
                raise ValueError(f"unknown spending strategy {strategy!r}")
            prev_real_spend = spend_real
            need = spend_real * infl
            pension = _pension_income(cfg, year, infl)
            mort_interest = mortgage * cfg.house["mortgage_rate"] if mortgage else 0.0
            # invest. income tax adds to the need (negative = refundable franking
            # credits in low-income retirement, which REDUCE the need).
            net_need = need - pension + mort_interest + extra_rent * infl + inv_tax
            withdrawal = max(0.0, net_need)
            short, wtax = _draw_need(bal, withdrawal, year, cfg, reserve, cost_base)
            # withdrawal tax (CGT + foreign-pension) adds to the need, drawn next (single-pass)
            if wtax > 0:
                short2, _ = _draw_need(bal, wtax, year, cfg, reserve, cost_base)
                short += short2
            row.need, row.pension_income, row.withdrawal = need, pension, withdrawal
            row.housing = mort_interest
            row.tax_paid = wtax + inv_tax
            row.net_cashflow = pension - need - mort_interest
            row.savings_in = -withdrawal             # net dis-saving (drawdown) in retirement
            if short > 1.0:
                depleted = True

            # ---- aged care ----
            # The recurrent incremental fees are cash-flow costs. Three fund modes:
            #  * 'portfolio' (BASE): draw the fees from the investible pool — the
            #    realistic default; you can't get equity out of a home you live in
            #    without borrowing, so the fees are paid from drawdown. Can deplete.
            #  * 'mortgage': borrow the fees against the home (mortgage += care), then
            #    service the INTEREST from the pool each year (the existing mort_interest
            #    path) — a real interest-only loan, principal settled from the estate.
            #    House market value stays intact but encumbered. NOT a reverse mortgage.
            #  * 'house': reverse-mortgage style — equity consumed, interest NOT serviced
            #    from cash. Kept for comparison; explicitly NOT the plan's intent.
            ac = cfg.aged_care
            if ac.get("enabled"):
                funded = ac.get("funded_from", "portfolio")
                care_per = ac["cost_per_person_today"] * ac["incremental_fraction"]
                care_total = 0.0
                # episode 1: older partner ~88; episode 2: Person 1 ~88
                if ac.get("episodes", 0) >= 1 and older_age in range(88, 88 + ac["episode_years"]):
                    care_total += care_per * (1 + care_infl) ** n
                if ac.get("episodes", 0) >= 2 and person1_age in range(88, 88 + ac["episode_years"]):
                    care_total += care_per * (1 + care_infl) ** n
                if care_total > 0:
                    row.care += care_total
                    if funded == "mortgage" and house_value > 0:
                        # Borrow against the home; interest is serviced from the pool
                        # next year onward via the mort_interest path (interest-only).
                        mortgage += care_total
                    elif funded == "house" and house_value > 0:
                        # Reverse-mortgage style: equity consumed, unserviced. Market
                        # value untouched; care is a permanent claim against equity.
                        care_drawn = min(house_value, care_drawn + care_total)
                    else:  # 'portfolio' (base): pay the fees out of investments
                        short_c, _ = _draw_need(bal, care_total, year, cfg, reserve, cost_base)
                        row.withdrawal += care_total
                        if short_c > 1.0:
                            depleted = True

        # ---- close: net worth ----
        drawpool = sum(v for k, v in bal.items())
        home_equity = max(0.0, house_value - care_drawn)   # market value net of care drawn
        nw_nom = drawpool + home_equity - mortgage
        row.accounts = dict(bal)
        row.house_value, row.mortgage = house_value, mortgage
        row.care_drawn, row.home_equity = care_drawn, home_equity
        emb_tax = _embedded_tax(bal, cost_base, cfg, year)
        row.drawpool = drawpool
        row.drawpool_today = drawpool / infl
        row.net_worth_nominal = nw_nom
        row.net_worth_today = nw_nom / infl
        row.embedded_tax = emb_tax
        row.net_worth_after_tax_today = (nw_nom - emb_tax) / infl
        row.depleted = depleted
        rows.append(row)
        if depleted:
            break

    return rows
