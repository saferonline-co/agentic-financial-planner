<!-- SAMPLE OUTPUT — a committed snapshot of `recommended-summary.md` generated from the
     fictional config.example.yaml, shown in the README so you can see what the model
     produces. Every figure is invented. Your real runs write to model/outputs/. -->

# Financial plan — scenario: recommended

**Income sustains 83%** of paths (need met every year from the investible pool) · capital preserved 60% · funded ratio 1.42

Median terminal **investible pool $3.73M** (P10 $0.01M · P90 $19.47M) — today's money, ex-house, 2086. _Total net worth incl. the ring-fenced home is shown below but is not spendable._

> **Run config:** equity 7.8% arith (~+3.9% real geo) · spend blanchett_smile base $90k · house $0.70M · inheritance $200k · Person 1 retires 2054 · 10,000 MC trials. Regenerate via `run.py`; do not hand-edit.

_All figures AUD. Deterministic central case unless noted; Monte Carlo = 10,000 correlated-lognormal trials. Today's money = nominal deflated by CPI._

## Timeline
- Person 2 retires 2052, Person 1 retires 2054 (horizon 2086, Person 1 age 92).
- House bought 2030 at $0.83M; paid off by 2054.
- Inheritance 2050 (variant: full).

## Net worth trajectory (today's money)
_Judge sustainability on the **investible pool** (income-generating capital). 'Net worth' also includes the home (kept fully owned in the base — aged care is paid from the pool, not by drawing the house). House (market) is the property's value; Home equity nets off any aged-care equity draw (equal in the base). After-tax = net of deferred tax on unrealised foreign-pension / ETF gains._
| Year | Phase | Net worth (gross) | After-tax | Investible pool | House (market) | Home equity (post aged-care) |
|---|---|---:|---:|---:|---:|---:|
| 2026 | working | $0.49M | $0.48M | $0.49M | $0.00M | $0.00M |
| 2031 | working | $0.83M | $0.81M | $0.72M | $0.77M | $0.77M |
| 2036 | working | $1.29M | $1.26M | $1.02M | $0.85M | $0.85M |
| 2041 | working | $1.85M | $1.82M | $1.44M | $0.94M | $0.94M |
| 2046 | working | $2.53M | $2.48M | $1.96M | $1.03M | $1.03M |
| 2051 | working | $3.52M | $3.45M | $2.79M | $1.13M | $1.13M |
| 2056 | retired | $3.89M | $3.82M | $2.64M | $1.25M | $1.25M |
| 2061 | retired | $4.04M | $3.96M | $2.66M | $1.38M | $1.38M |
| 2066 | retired | $4.28M | $4.19M | $2.76M | $1.52M | $1.52M |
| 2071 | retired | $4.58M | $4.49M | $2.91M | $1.67M | $1.67M |
| 2076 | retired | $4.97M | $4.86M | $3.13M | $1.84M | $1.84M |
| 2081 | retired | $5.10M | $4.99M | $3.07M | $2.03M | $2.03M |
| 2086 | retired | $5.19M | $5.09M | $2.96M | $2.23M | $2.23M |

## Retirement spend (glidepath, today's money)
| Year | Older age | Real need |
|---|---:|---:|
| 2055 | 63 | $90k |
| 2062 | 70 | $90k |
| 2068 | 76 | $79k |
| 2086 | 94 | $68k |

## Monte Carlo
- Probability income sustains (never depletes the pool): **83%**
- Capital preserved (terminal pool ≥ 85% of start): **60%**
- Terminal **investible pool** (today): P10 $0.01M · P50 $3.73M · P90 $19.47M
- Terminal net worth incl. home (today): P10 $1.03M · P50 $5.75M · P90 $21.82M
- Median depletion year (failing paths): 2080
- _Backstop not in the failure metric: a 'depleted' path still owns the home (~$2.23M equity today at horizon, after aged-care draws). Downsizing / a reverse mortgage would lift real-world resilience above the % above._

- Deterministic terminal (central): $5.19M; funded ratio 1.42 (>1.0 = fully funded, discounted at the AUD real risk-free rate).

## Assumptions (documented)
- Inflation: CPI 2.5%, earnings 3.8%, care 5.0%.
- Home price growth (decoupled from the property CMA): then +2% real.
- Foreign state pensions FROZEN nominal (AU-resident); super earnings taxed 15% accumulation / 0% pension; full AU income tax on gross salary.
- House ring-fenced as the aged-care reserve (RAD refundable).
- Simplifications: franking credits and foreign-pension foreign-income tax approximated; CGT single-pass. See README.