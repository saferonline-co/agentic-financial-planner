"""Human-readable markdown summary of a scenario result."""
from __future__ import annotations

from ..analysis import ScenarioResult
from ..events import retirement_year


def _m(x: float) -> str:
    return f"${x/1e6:.2f}M"


def summary(result: ScenarioResult) -> str:
    cfg, rows, mc = result.cfg, result.rows, result.mc
    retire = retirement_year(cfg)
    horizon = cfg.horizon_year
    last = rows[-1]
    L: list[str] = []

    eq = cfg.assumptions["cma"]["asset_classes"]["equity"]["mean"]
    eq_real = eq - 0.5 * cfg.assumptions["cma"]["asset_classes"]["equity"]["sd"] ** 2 \
        - cfg.assumptions["inflation"]["cpi"]
    house_px = cfg.house["target_price_today"] if cfg.house else 0
    inh = cfg.inheritance["variants"][cfg.inheritance["selected"]]
    spend = cfg.raw["retirement_spending"]

    L.append(f"# Financial plan — scenario: {result.name}")
    L.append("")
    # Lead with INCOME SUSTAINABILITY off the investible pool (the decision metric),
    # not total net worth (which includes the ring-fenced, unspendable home).
    L.append(
        f"**Income sustains {mc.p_sustains:.0%}** of paths (need met every year from the "
        f"investible pool) · capital preserved {mc.p_capital_preserved:.0%} · "
        f"funded ratio {result.funded_ratio:.2f}"
    )
    L.append("")
    L.append(
        f"Median terminal **investible pool {_m(mc.pool_p50)}** (P10 {_m(mc.pool_p10)} · "
        f"P90 {_m(mc.pool_p90)}) — today's money, ex-house, {horizon}. "
        f"_Total net worth incl. the ring-fenced home is shown below but is not spendable._"
    )
    L.append("")
    # Config stamp — what produced these numbers (outputs are build artifacts).
    L.append(
        f"> **Run config:** equity {eq:.1%} arith (~{eq_real:+.1%} real geo) · "
        f"spend {spend['strategy']} base ${spend['base']/1e3:.0f}k · "
        f"house ${house_px/1e6:.2f}M · inheritance ${inh/1e3:.0f}k · "
        f"Person 1 retires {retire} · {mc.trials:,} MC trials. "
        f"Regenerate via `run.py`; do not hand-edit."
    )
    L.append("")
    L.append("_All figures AUD. Deterministic central case unless noted; Monte Carlo "
             f"= {mc.trials:,} correlated-lognormal trials. Today's money = nominal deflated by CPI._")
    L.append("")

    L.append("## Timeline")
    L.append(f"- Person 2 retires {cfg.events['person2_retires']['year']}, Person 1 retires {retire} "
             f"(horizon {horizon}, Person 1 age {cfg.age('person1', horizon)}).")
    if cfg.house:
        hr = next((r for r in rows if r.year == cfg.events["house_purchase"]["year"]), None)
        if hr:
            L.append(f"- House bought {hr.year} at {_m(hr.house_value)}; "
                     f"paid off by {retire}.")
    L.append(f"- Inheritance {cfg.events['inheritance']['year']} "
             f"(variant: {cfg.inheritance['selected']}).")
    L.append("")

    L.append("## Net worth trajectory (today's money)")
    L.append("_Judge sustainability on the **investible pool** (income-generating capital). "
             "'Net worth' also includes the home (kept fully owned in the base — aged care is "
             "paid from the pool, not by drawing the house). House (market) is the property's "
             "value; Home equity nets off any aged-care equity draw (equal in the base). "
             "After-tax = net of deferred tax on unrealised foreign-pension / ETF gains._")
    L.append("| Year | Phase | Net worth (gross) | After-tax | Investible pool "
             "| House (market) | Home equity (post aged-care) |")
    L.append("|---|---|---:|---:|---:|---:|---:|")
    years = list(range(cfg.start_year, horizon + 1, 5))
    if years[-1] != horizon:
        years.append(horizon)
    for y in years:
        r = next((r for r in rows if r.year == y), None)
        if r:
            L.append(f"| {y} | {r.phase} | {_m(r.net_worth_today)} | "
                     f"{_m(r.net_worth_after_tax_today)} | "
                     f"{_m(r.drawpool_today)} | {_m(r.house_value/r.infl)} | "
                     f"{_m(r.home_equity/r.infl)} |")
    L.append("")

    L.append("## Retirement spend (glidepath, today's money)")
    L.append("| Year | Older age | Real need |")
    L.append("|---|---:|---:|")
    for y in [retire + 1, retire + 8, retire + 14, horizon]:
        r = next((r for r in rows if r.year == y), None)
        if r and r.need:
            L.append(f"| {y} | {r.older_age} | ${r.need/r.infl/1e3:,.0f}k |")
    L.append("")

    L.append("## Monte Carlo")
    L.append(f"- Probability income sustains (never depletes the pool): **{mc.p_sustains:.0%}**")
    L.append(f"- Capital preserved (terminal pool ≥ "
             f"{cfg.monte_carlo['capital_preserved_fraction']:.0%} of start): "
             f"**{mc.p_capital_preserved:.0%}**")
    L.append(f"- Terminal **investible pool** (today): P10 {_m(mc.pool_p10)} · "
             f"P50 {_m(mc.pool_p50)} · P90 {_m(mc.pool_p90)}")
    L.append(f"- Terminal net worth incl. home (today): P10 {_m(mc.terminal_p10)} · "
             f"P50 {_m(mc.terminal_p50)} · P90 {_m(mc.terminal_p90)}")
    if mc.median_depletion_year:
        L.append(f"- Median depletion year (failing paths): {mc.median_depletion_year}")
    if cfg.house:
        L.append(f"- _Backstop not in the failure metric: a 'depleted' path still owns the "
                 f"home (~{_m(last.home_equity/last.infl)} equity today at horizon, after "
                 f"aged-care draws). Downsizing / a reverse mortgage would lift real-world "
                 f"resilience above the % above._")
    L.append("")
    L.append(f"- Deterministic terminal (central): {_m(last.net_worth_today)}; "
             f"funded ratio {result.funded_ratio:.2f} "
             f"(>1.0 = fully funded, discounted at the AUD real risk-free rate).")
    L.append("")
    L.append("## Assumptions (documented)")
    inf = cfg.assumptions["inflation"]
    L.append(f"- Inflation: CPI {inf['cpi']:.1%}, earnings {inf['earnings']:.1%}, "
             f"care {inf['care_cost']:.1%}.")
    if cfg.house and cfg.house.get("growth"):
        regimes = []
        for g in cfg.house["growth"]:
            rate = (f"{g['nominal']:+.0%} nom" if "nominal" in g
                    else f"{g['real']:+.0%} real")
            regimes.append(f"to {g['until_year']}: {rate}" if g.get("until_year")
                           else f"then {rate}")
        L.append("- Home price growth (decoupled from the property CMA): "
                 + "; ".join(regimes) + ".")
    L.append("- Foreign state pensions FROZEN nominal (AU-resident); super earnings taxed "
             "15% accumulation / 0% pension; full AU income tax on gross salary.")
    L.append("- House ring-fenced as the aged-care reserve (RAD refundable).")
    L.append("- Simplifications: franking credits and foreign-pension foreign-income tax "
             "approximated; CGT single-pass. See README.")
    return "\n".join(L)
