# Lifetime cash-flow model

A config-driven, deterministic **and** Monte Carlo lifetime financial-planning
model (AUD by convention). Built on the recognised industry standard — a
**cash-flow-based forward simulator** with a fixed annual order-of-operations
(the method used by Voyant / eMoney / RightCapital / ProjectionLab and expected
by FCA FG22/5, CFP Practice Standard C.4, ISO 22222).

It models two people (`person1`, `person2`), full Australian-resident tax,
per-bucket drawdown under super-access constraints, a Blanchett spending
glidepath, stress overlays, and an actuarial funded ratio. Output is
decision-support, **not financial advice** — confirm material tax/structure
assumptions with a licensed adviser.

## Configure

All inputs live in `config/personal/config.yaml` (git-ignored) — the package hard-codes no figures.

- `config/config.skeleton.yaml` is the tracked, personal-data-free **template**:
  structure present, every personal value `null`. Copy it into the git-ignored
  `config/personal/` folder (so your real figures never get committed) and fill that
  in — open the project in Claude Code and say "help me set up my plan", or copy and
  edit by hand: `cp config/config.skeleton.yaml config/personal/config.yaml`.
- `config/config.example.yaml` is a **complete, fictional, working** config you can
  run immediately to see what the model does and what good input looks like.

## Run

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
# Try the worked example immediately:
.venv/bin/python run.py --config config.example.yaml --scenario recommended
.venv/bin/python run.py --config config.example.yaml --scenario all --trials 5000
# Set up your own plan (creates the git-ignored personal/config.yaml from the skeleton):
cp config/config.skeleton.yaml config/personal/config.yaml   # then fill it in (or let Claude)
# Once it's filled, run against your own data (it is the default config):
.venv/bin/python run.py --scenario recommended
.venv/bin/python run.py --scenario recommended --chart    # + PNG chart (assets & cash flows)
.venv/bin/python -m pytest                                 # the test suite (TDD)
```

Outputs land in `outputs/`: a markdown summary per scenario + a combined
`scenarios.xlsx` (Summary grid, MonteCarlo sheet, and a per-scenario annual
ledger in the years-as-columns layout — Assets / Liabilities / Net assets →
Inflows / Outflows → **Net inflow (cash-flow)** → **Net worth** → today's money).

## Structure

```
config/config.skeleton.yaml the tracked template (all-null); copy into personal/ and fill in
config/personal/config.yaml YOUR inputs — git-ignored (the single source of truth; no numbers in code)
config/config.example.yaml  a complete, fictional, runnable example
config/config.test.yaml      a stable fixture the test suite asserts against
config/scenarios.yaml        named sparse overrides (recommended, retire_earlier, rent_forever, ...)
finmodel/                    the engine package
  schema.py  events.py  accounts(in schema)  returns.py  tax.py  spending.py
  engine.py  montecarlo.py  metrics.py  stress.py  analysis.py  report/
tests/                       pytest suite (built test-first; runs against config.test.yaml)
```

## Method (annual order-of-operations)

Per year: open balances → index income/expenses for inflation (each at its own
rate: CPI / earnings / care) → recognise gross income → expenses & debt → **tax**
→ net cash → allocate (surplus to savings; shortfall to a drawdown waterfall that
**respects super access** — a super pot is locked until its `access_year`) → grow
each account at its allocation-derived return → close. Compute nominal; report
today's money.

- **Deterministic** = central case + a low/intermediate/high ±3% band (FCA COBS 13).
- **Monte Carlo** = correlated **lognormal** draws from arithmetic-mean Capital
  Market Assumptions + a correlation matrix; reports probability of success,
  capital-preserved %, and terminal P10/P50/P90.
- **Funded ratio** (actuarial complement) = PV(assets + reliable income) /
  PV(spending), discounted at the real risk-free rate.
- **Stress** overlays: year-1 crash, sustained-low returns, high inflation,
  longevity tail, house-price corrections, aged-care-from-pool.
- **Spending**: Blanchett smile (default glidepath), constant-real, Guyton-Klinger
  guardrails, Vanguard dynamic — all config-selectable.

## Tax (full AU, params in `config.tax`)

Income tax + Medicare on **gross** salary; super contributions tax (15% + Div293);
super earnings tax (15% accumulation / 0% pension); Div296; CGT (50% discount, with
a regime-change indexation toggle). The defaults are Australian resident; replace
the `tax` block to model another jurisdiction.

### Documented simplifications

- Per-person take-home can be calibrated to known payslips via the `other_deductions`
  line (post-tax, consumed: e.g. study-loan repayments / insurance / unmodelled
  salary packaging). Without it the raw tax calc may over-state take-home and
  savings.
- Franking credits and foreign-pension income tax are approximated; CGT is a
  single-pass (no second-order tax-on-tax). Div296 only bites above $3m super.
- House price is set in today's money and grown at the growth schedule to the
  purchase year.

## Updating

Change assumptions or tax law by editing `config/personal/config.yaml` (data only — the
package has no hard-coded figures). Add a scenario by adding a sparse override to
`config/scenarios.yaml`. Re-run `pytest` after any change.
