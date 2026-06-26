"""Time-series chart of a scenario's deterministic-central path: asset levels
(top panel) and annual cash flows (bottom panel), in today's money.

Two stacked panels sharing one x-axis, rather than a dual-axis overlay, because the
series are different *kinds* of quantity on different scales: asset *levels* are
stocks in the millions; annual *flows* (saving, housing outlay, care) are rates in
the tens of thousands. Separating them removes the dual-axis "which line is on which
axis?" load while the shared time axis (and the event markers spanning both panels)
keeps the relationship — e.g. the house purchase dipping net worth *and* spiking the
housing flow — visible.

Reads `ScenarioResult.rows` (the deterministic central ledger) — not Monte Carlo,
so it's a single clean line per series. Headless (Agg backend); writes a PNG.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..events import resolve_events

# accounts that make up "investments" (everything investible except cash)
_INVEST = ("etf", "person1_super", "person2_super", "person1_foreign_pension",
           "person2_foreign_pension", "person1_taxfree", "foreign_property")


def write_chart(result, path: str) -> str:
    rows = result.rows
    years = [r.year for r in rows]

    def today(v, infl):                       # nominal -> today's money
        return v / infl if infl else 0.0

    invest = [today(sum(r.accounts.get(k, 0.0) for k in _INVEST), r.infl) / 1e6 for r in rows]
    cash   = [today(r.accounts.get("cash", 0.0), r.infl) / 1e6 for r in rows]
    house  = [today(r.house_value, r.infl) / 1e6 for r in rows]    # market value (one object)
    house_eq = [today(r.home_equity, r.infl) / 1e6 for r in rows]  # net of any equity draw
    drew_house = any(r.care_drawn > 0 for r in rows)   # care consumed home equity (house mode)
    networth = [today(r.net_worth_today, 1.0) / 1e6 for r in rows]   # already today's $
    saving   = [today(r.savings_in, r.infl) / 1e3 for r in rows]   # +accum / -draw
    house_in = [today(r.house_in, r.infl) / 1e3 for r in rows]
    care     = [today(r.care, r.infl) / 1e3 for r in rows]         # aged-care cost (a 2nd object)
    has_care = any(c > 0 for c in care)

    # Two stacked panels sharing the x-axis: levels on top (taller), flows below.
    fig, (axL, axF) = plt.subplots(2, 1, sharex=True, figsize=(12, 8),
                                   gridspec_kw={"height_ratios": [3, 2]})

    # ---- top panel: asset levels — all SOLID ($M, today's money) ----
    axL.plot(years, networth, color="#111111", lw=2.8, label="Net worth (total)")
    axL.plot(years, invest, color="#1f77b4", lw=2.2, label="Investments (super, pensions, ETF, Tax-free)")
    axL.plot(years, house,  color="#2ca02c", lw=2.0, label="House — market value")
    if drew_house:   # only when aged care consumed home equity (funded_from: house)
        axL.plot(years, house_eq, color="#2ca02c", lw=1.6, ls=(0, (4, 2)),
                 label="House — equity after aged-care draws")
    axL.plot(years, cash,   color="#9467bd", lw=1.8, label="Cash")
    axL.set_ylabel("Today's $M", fontsize=11)
    axL.grid(True, alpha=0.25)
    axL.set_ylim(bottom=0)
    axL.set_title("Asset values — what the household owns over time", fontsize=11)
    axL.legend(loc="upper left", fontsize=9, framealpha=0.9)

    # ---- bottom panel: annual cash flows — all DASHED ($k/yr, today's money) ----
    axF.plot(years, saving, color="#d62728", lw=2.0, ls="--",
             label="Into savings (+) / drawdown (−)")
    axF.plot(years, house_in, color="#ff7f0e", lw=2.0, ls="--",
             label="Into house (deposit / payoff)")
    if has_care:   # aged care as its own object: a separate cost flow ($k/yr)
        axF.plot(years, care, color="#8c564b", lw=2.0, ls="--",
                 label="Aged-care cost (funded from pool)")
    axF.axhline(0, color="#888", lw=0.8, ls=":")
    axF.set_ylabel("Today's $k", fontsize=11)
    axF.set_xlabel("Year")
    axF.grid(True, alpha=0.25)
    axF.set_title("Cash flow — money into and out of the pool each year", fontsize=11)
    axF.legend(loc="upper left", fontsize=9, framealpha=0.9)

    # ---- event markers spanning both panels (label them once, on the top panel) ----
    ev = resolve_events(result.cfg)
    top = axL.get_ylim()[1]
    for yr, lbl, frac in ((ev.get("house_purchase"), "House bought", 0.40),
                          (ev.get("person2_retires"), "Person 2 retires", 0.62),
                          (ev.get("person1_retires"), "Person 1 retires", 0.40)):
        if yr:
            for ax in (axL, axF):
                ax.axvline(yr, color="#555", lw=0.8, ls="--", alpha=0.5)
            axL.text(yr, top * frac, f" {lbl}", rotation=90,
                     va="bottom", ha="right", fontsize=8, color="#555")

    fig.suptitle(f"{result.name} — deterministic central path (today's money)",
                 fontsize=12, y=0.995)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path
