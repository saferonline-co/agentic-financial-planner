"""Australian tax engine (resident). Planning approximation of the major levers.

All parameters come from cfg.tax (so law changes are data edits). Covers:
income tax + Medicare, super contributions tax (15% + Div293), super earnings
tax (15% accumulation / 0% pension), Div296 (>$3m), CGT (50% discount or 2027
indexation toggle), franking credits. Simplifications are documented in output.
"""
from __future__ import annotations

from .schema import Config


def income_tax(taxable: float, cfg: Config) -> float:
    """Progressive bracket tax (excludes Medicare)."""
    if taxable <= 0:
        return 0.0
    brackets = cfg.tax["income_brackets"]
    tax_due = 0.0
    lower = 0.0
    for b in brackets:
        up_to = b["up_to"]
        cap = float(up_to) if up_to is not None else float("inf")
        if taxable > lower:
            slice_amt = min(taxable, cap) - lower
            tax_due += slice_amt * b["rate"]
            lower = cap
        if taxable <= cap:
            break
    return tax_due


def medicare(taxable: float, cfg: Config) -> float:
    if taxable <= 0:
        return 0.0
    return taxable * cfg.tax["medicare_levy"]


def total_income_tax(taxable: float, cfg: Config) -> float:
    return income_tax(taxable, cfg) + medicare(taxable, cfg)


def take_home(gross: float, concessional: float, cfg: Config) -> float:
    """Net cash to the household from employment.

    Concessional super (salary sacrifice + SG) is pre-tax: it reduces taxable
    income and is taxed inside the fund (see super_contributions_tax), so it is
    NOT part of take-home cash.
    """
    taxable = max(0.0, gross - concessional)
    return taxable - total_income_tax(taxable, cfg)


def super_contributions_tax(concessional: float, income: float, cfg: Config) -> float:
    s = cfg.tax["super"]
    rate = s["contributions_tax"]
    if income > s["div293_threshold"]:
        rate += s["div293_extra"]
    return concessional * rate


def super_earnings_rate(phase: str, cfg: Config) -> float:
    """Tax rate on super fund earnings: 15% accumulation, 0% pension phase."""
    s = cfg.tax["super"]
    return s["earnings_tax_accum"] if phase == "accumulation" else s["earnings_tax_pension"]


def div296_extra_tax(super_balance: float, earnings: float, cfg: Config) -> float:
    """Extra 15% on earnings attributable to a super balance above $3m."""
    s = cfg.tax["super"]
    threshold = s["div296_threshold"]
    if super_balance <= threshold or earnings <= 0:
        return 0.0
    proportion = (super_balance - threshold) / super_balance
    return earnings * proportion * s["div296_extra"]


def marginal_on_top(other_taxable: float, extra: float, cfg: Config) -> float:
    """Incremental income tax (incl. Medicare) on `extra` assessable income stacked
    on top of `other_taxable` — i.e. taxed at the person's true marginal rate."""
    if extra <= 0:
        return 0.0
    return total_income_tax(other_taxable + extra, cfg) - total_income_tax(other_taxable, cfg)


def investment_income_tax(cash_bal: float, etf_bal: float, etf_alloc: dict,
                          yields: dict, other_taxable: dict, cfg: Config) -> tuple[float, float]:
    """Annual tax on ONGOING investment income (not capital growth):
      * cash interest + ETF bond coupons -> ordinary income
      * ETF equity dividends -> franked on the AU share (franking_ratio); franking
        credits gross up assessable income and offset tax (refundable -> can go
        negative in low-income years).
    Joint holdings are split 50/50 across the two people and taxed at each one's
    marginal rate (stacked on their other assessable income). Returns
    (net_tax, etf_income) where etf_income is the distribution reinvested (which
    lifts the ETF cost base, so it is not later double-taxed as CGT)."""
    eq = etf_alloc.get("equity", 0.0)
    bd = etf_alloc.get("bond", 0.0)
    interest = cash_bal * yields["cash"] + etf_bal * bd * yields["bond"]
    dividends = etf_bal * eq * yields["equity"]
    etf_income = etf_bal * (bd * yields["bond"] + eq * yields["equity"])
    fr = cfg.tax.get("franking_ratio", 0.0)
    ctr = cfg.tax.get("company_tax_rate", 0.30)
    franking_credit = dividends * fr * ctr / (1.0 - ctr)
    assessable = interest + dividends + franking_credit          # grossed up
    net = 0.0
    for person in ("person1", "person2"):
        net += (marginal_on_top(other_taxable.get(person, 0.0), assessable * 0.5, cfg)
                - franking_credit * 0.5)
    return net, etf_income


def cgt_on_withdrawal(
    withdrawal: float, gain_fraction: float, marginal_rate: float, cfg: Config,
    year: int | None = None,
) -> float:
    """CGT on realising `withdrawal` from a parcel that is `gain_fraction` gain.

    Discount method: 50% discount on the gain, taxed at the member's marginal
    rate. (Indexation method is a config toggle for the 2027 budget change.)

    Proposed 2027 regime (`cgt.enabled_2027`, year >= `cgt.change_year`): the 50%
    discount is removed and a minimum 30% tax applies, i.e. the gain is taxed at
    max(marginal_rate, min_rate). Cost-base indexation relief is approximated as
    nil (conservative — slightly overstates the tax).
    """
    gain = withdrawal * gain_fraction
    if gain <= 0:
        return 0.0
    c = cfg.tax["cgt"]
    if (c.get("enabled_2027") and year is not None
            and year >= c.get("change_year", 9999)):
        return gain * max(marginal_rate, c.get("min_rate", 0.30))
    if c["method"] == "discount":
        taxable_gain = gain * (1.0 - c["discount"])
    else:  # indexation: approximate as full gain (indexation handled upstream)
        taxable_gain = gain
    return taxable_gain * marginal_rate
