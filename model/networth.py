#!/usr/bin/env python
"""Print net worth every N years for a scenario (deterministic central case).

  .venv/bin/python networth.py                      # recommended, every 5 years
  .venv/bin/python networth.py house_dearer          # a named scenario
  .venv/bin/python networth.py recommended 10        # every 10 years
"""
import sys

from finmodel import schema, engine
from finmodel.returns import DeterministicReturns


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "recommended"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    cfg = schema.load_config(scenario=name)
    rows = engine.run(cfg, DeterministicReturns(cfg, "central"))

    print(f"{name} — net worth every {step} years (today's money, deterministic central)")
    print(f"{'year':>5} {'P1':>4} {'phase':9} {'gross NW':>10} {'after-tax':>10} "
          f"{'investible':>11} {'house':>9}")
    for r in rows:
        if (r.year - cfg.start_year) % step == 0 or r.year == rows[-1].year:
            print(f"{r.year:>5} {r.person1_age:>4} {r.phase:9} "
                  f"${r.net_worth_today/1e6:>7.2f}M ${r.net_worth_after_tax_today/1e6:>7.2f}M "
                  f"${r.drawpool_today/1e6:>8.2f}M ${r.house_value/r.infl/1e6:>6.2f}M")


if __name__ == "__main__":
    main()
