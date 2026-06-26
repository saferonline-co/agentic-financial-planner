#!/usr/bin/env python
"""CLI: run one or all scenarios -> markdown summaries + a combined Excel workbook.

  python run.py --scenario recommended
  python run.py --scenario all --trials 5000
  python run.py --config config.example.yaml --scenario recommended   # try the demo
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from finmodel import analysis, schema, stress
from finmodel.report import charts, excel, markdown

CONFIG_DIR = Path(__file__).resolve().parent / "config"
OUT_DIR = Path(__file__).resolve().parent / "outputs"


def scenario_names() -> list[str]:
    with open(CONFIG_DIR / "scenarios.yaml") as fh:
        data = yaml.safe_load(fh) or {}
    return list((data.get("scenarios") or {}).keys())


def main():
    ap = argparse.ArgumentParser(description="Lifetime cash-flow model")
    ap.add_argument("--scenario", default="recommended",
                    help="scenario name, or 'all'")
    ap.add_argument("--config", default=None,
                    help="config file: a path, or a name resolved under config/ "
                         "(defaults to config.yaml; use config.example.yaml for the demo)")
    ap.add_argument("--trials", type=int, default=None, help="Monte Carlo trials")
    ap.add_argument("--outdir", default=str(OUT_DIR))
    ap.add_argument("--chart", action="store_true",
                    help="also write a PNG chart (assets + cash flows over time) per scenario")
    args = ap.parse_args()

    cfg_path = None
    if args.config:
        p = Path(args.config)
        cfg_path = p if p.exists() else CONFIG_DIR / args.config
    elif not (CONFIG_DIR / "personal" / "config.yaml").exists():
        # Fresh clone: the user hasn't created their personal config yet.
        ap.exit(2, (
            "No config/personal/config.yaml yet — that's the file that holds your plan.\n"
            "  • Set it up with Claude: open this project and say "
            "\"help me set up my plan\".\n"
            "  • Or start from the skeleton: "
            "cp config/config.skeleton.yaml config/personal/config.yaml  (then edit it).\n"
            "  • Or just try the demo now: "
            "run.py --config config.example.yaml --scenario recommended\n"))

    names = scenario_names() if args.scenario == "all" else [args.scenario]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Layout: top-level holds only the headline artifacts (the combined
    # scenarios.xlsx + the `recommended` summary/workbook); every other
    # scenario-specific file lives under outputs/scenarios/.
    scen_dir = outdir / "scenarios"
    scen_dir.mkdir(parents=True, exist_ok=True)
    TOP_LEVEL = {"recommended"}

    def dir_for(name: str) -> Path:
        return outdir if name in TOP_LEVEL else scen_dir

    results = []
    print(f"{'scenario':22} {'sustains':>9} {'preserved':>10} {'funded':>7} {'P50 terminal':>14}")
    for name in names:
        cfg = schema.load_config(scenario=name, config_path=cfg_path)
        res = analysis.analyse(cfg, scenario_name=name, trials=args.trials)
        results.append(res)
        md = markdown.summary(res)
        (dir_for(name) / f"{name}-summary.md").write_text(md)
        if args.chart:
            charts.write_chart(res, str(dir_for(name) / f"{name}-chart.png"))
        print(f"{name:22} {res.mc.p_sustains:>8.0%} {res.mc.p_capital_preserved:>9.0%} "
              f"{res.funded_ratio:>7.2f} {res.mc.terminal_p50/1e6:>12.2f}M")

    # Combined workbook → top level; a single-scenario run → that scenario's dir.
    xlsx = (outdir / "scenarios.xlsx" if len(results) > 1
            else dir_for(names[0]) / f"{names[0]}.xlsx")
    excel.write_report(str(xlsx), results)

    # FCA-style stress table for the (first) scenario
    print("\nStress overlays (deterministic central, terminal today's money):")
    for s in stress.run(results[0].cfg):
        flag = "DEPLETED" if s.depleted else "ok"
        print(f"  {s.name:16} {s.terminal_today/1e6:>7.2f}M  {flag}")

    print(f"\nWrote {len(results)} summary(s) + {xlsx.name} to {outdir}")


if __name__ == "__main__":
    main()
