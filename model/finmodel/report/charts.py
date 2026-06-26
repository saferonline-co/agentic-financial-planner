"""Time-series chart of a scenario's deterministic-central path: asset levels
(left axis) and annual cash flows (right axis), in today's money.

Two y-axes because the series live on different scales: asset *levels* are in the
millions; annual *flows* (saving, housing outlay) are in the tens of thousands.

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

    fig, axL = plt.subplots(figsize=(12, 6.5))
    axR = axL.twinx()

    # ---- left axis: asset levels — all SOLID ($M, today's money) ----
    lines = []
    lines += axL.plot(years, networth, color="#111111", lw=2.8, label="Net worth (total)")
    lines += axL.plot(years, invest, color="#1f77b4", lw=2.2, label="Investments (super, pensions, ETF, Tax-free)")
    lines += axL.plot(years, house,  color="#2ca02c", lw=2.0, label="House — market value")
    if drew_house:   # only when aged care consumed home equity (funded_from: house)
        lines += axL.plot(years, house_eq, color="#2ca02c", lw=1.6, ls=(0, (4, 2)),
                          label="House — equity after aged-care draws")
    lines += axL.plot(years, cash,   color="#9467bd", lw=1.8, label="Cash")
    axL.set_ylabel("Asset value — today's $M", fontsize=11)
    axL.set_xlabel("Year")
    axL.grid(True, alpha=0.25)
    axL.set_ylim(bottom=0)

    # ---- right axis: annual cash flows — all DASHED ($k/yr, today's money) ----
    sline, = axR.plot(years, saving, color="#d62728", lw=2.0, ls="--",
                      label="Into savings (+) / drawdown (−)")
    hline, = axR.plot(years, house_in, color="#ff7f0e", lw=2.0, ls="--",
                      label="Into house (deposit / payoff)")
    flows = [sline, hline]
    if has_care:   # aged care as its own object: a separate cost flow ($k/yr)
        cline, = axR.plot(years, care, color="#8c564b", lw=2.0, ls="--",
                          label="Aged-care cost (funded from pool)")
        flows.append(cline)
    axR.axhline(0, color="#888", lw=0.8, ls=":")
    axR.set_ylabel("Annual cash flow — today's $k", fontsize=11)

    # ---- event markers (house purchase & Person 2 retirement share 2031 -> stagger labels) ----
    ev = resolve_events(result.cfg)
    top = axL.get_ylim()[1]
    for yr, lbl, frac in ((ev.get("house_purchase"), "House bought", 0.40),
                          (ev.get("person2_retires"), "Person 2 retires", 0.62),
                          (ev.get("person1_retires"), "Person 1 retires", 0.40)):
        if yr:
            axL.axvline(yr, color="#555", lw=0.8, ls="--", alpha=0.5)
            axL.text(yr, top * frac, f" {lbl}", rotation=90,
                     va="bottom", ha="right", fontsize=8, color="#555")

    # ---- single grouped legend (top-left): solid levels first, then dashed flows,
    # each under a bold header naming its axis & units ----
    from matplotlib.lines import Line2D
    H_LEVELS = "Point-in-time values ($M, left axis)"
    H_FLOWS  = "Annual cash flow ($k/yr, right axis)"
    header = lambda txt: Line2D([], [], color="none", label=txt)  # invisible glyph = a header
    handles = [header(H_LEVELS)] + lines + [header(H_FLOWS)] + flows
    leg = axL.legend(handles, [h.get_label() for h in handles],
                     loc="upper left", fontsize=9, framealpha=0.9)
    for t in leg.get_texts():                       # bold the two group headers
        if t.get_text() in (H_LEVELS, H_FLOWS):
            t.set_fontweight("bold")

    axL.set_title(f"{result.name} — assets & cash flows over time (deterministic central, today's money)",
                  fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path
