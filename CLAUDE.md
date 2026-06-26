# Financial Planning — Project Guide

A config-driven lifetime cash-flow **model** for a household (two people), its
scenarios, and supporting method docs. This file is the **entry point**: it holds the
project's *purpose, rules, and pointers*, and the **onboarding instructions** Claude
follows to help a new user set up their plan.

This is a **template**. It ships with a skeleton config to fill in and a complete
fictional example to learn from. Output is decision-support, **not financial advice** —
material tax/structure assumptions must be confirmed with a licensed adviser.

---

## What this project is

A decision-support model that answers questions like:

1. **Can we retire when we want** with the lifestyle we want?
2. **Capital preservation** — does our income (investments + pensions + super) cover our
   target retirement spend *without* prematurely exhausting capital?

It answers these deterministically (central + a low/intermediate/high band) and via Monte
Carlo, with full Australian-resident tax, per-bucket drawdown under super-access
constraints, a spending glidepath, stress overlays, and an actuarial funded ratio. The tax
defaults are Australian; replace the `tax` block in the config to model another country.

## Goals

> _This section is intentionally blank. During onboarding, record the user's goals here —
> e.g. target retirement ages, target annual spend, home/rent intentions, and whether the
> priority is preserving capital or spending it down. Keep it short and specific._

## Using the model

- **The engine lives in `model/`.** All inputs are in `model/config/personal/config.yaml`
  (your data — git-ignored; copied from the tracked `config.skeleton.yaml`) and
  `model/config/scenarios.yaml` (sparse "what if" overrides). The package hard-codes no
  figures. A complete worked example is in `model/config/config.example.yaml`.
- **Set up the venv:** `cd model && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- **Run the example now:** `model/.venv/bin/python model/run.py --config config.example.yaml --scenario recommended`
- **Run your own plan (once `personal/config.yaml` is filled):** `model/.venv/bin/python model/run.py --scenario all`.
  Single scenario: `--scenario recommended`. Outputs → `model/outputs/` (markdown summaries
  + xlsx). **Generated — never hand-edit; regenerate.**
- **Tests:** `cd model && .venv/bin/python -m pytest -q`. TDD — write the test first. (Tests
  run against `config.example.yaml`.)
- **Method + structure:** `model/README.md`.
- **Why an assumption is what it is:** `model/DECISIONS.md` — dated, append-only. Add an
  entry whenever you change a non-obvious assumption.

## First-run onboarding (for Claude)

This is an agentic setup: **the user talks, you do the work** — create the environment, copy
files, ask questions, fill the config, run it. Don't make the user run commands or edit YAML;
do it for them with your tools and confirm as you go.

**Trigger.** Treat openers like **"Let's start"**, **"help me set up my plan"**, "get started",
or "set up my plan" — and any arrival where `model/config/personal/config.yaml` is missing or
still has `null` mandatory fields — as the cue to begin onboarding. On a fresh clone that file
won't exist yet; only the tracked `config.skeleton.yaml` does (step 2 creates the user's copy
from it). Greet briefly, say what you're about to do, then proceed **in order**:

0. **Set up the environment for them.** If `model/.venv` doesn't exist, create it and install
   deps: `cd model && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
   Then offer to run the fictional demo so they see what the model produces before entering
   anything: `model/.venv/bin/python model/run.py --config config.example.yaml --scenario recommended`.
1. **Start with goals.** Before any numbers, ask what they want the plan to tell them. Lead
   with a concrete example: *"What age would you like to retire at?"* Then draw out: the
   other partner's target retirement age; the annual spending they want in retirement
   (today's money); whether they plan to buy a home (and when) or keep renting; and whether
   their priority is **preserving capital** or **spending it down** over their lifetime.
   Write the answers into the **## Goals** section above.
2. **Create and fill the mandatory config.** First copy the tracked, all-null template
   into the user's own (git-ignored) `personal/` folder so their real figures are never
   committed: `cp model/config/config.skeleton.yaml model/config/personal/config.yaml`.
   Then walk through that `config.yaml` section by section, writing values as you go. The
   fields that are `null` (marked `# FILL`) are mandatory:
   - **people** — each person's birth year (`dob`), super preservation age, state-pension age.
   - **accounts** — balances for cash, taxable investments (etf), and each person's super;
     add the optional account types (foreign pension, tax-free wrapper, a property being
     sold) only if they apply, and delete the rest. Each account needs `balance`,
     `access_year`, `owner`.
   - **reserve_floor** — the minimum cash buffer to never draw below.
   - **pensions** — each person's state/foreign pension start year and annual amount (set
     `amount_today: 0` if none).
   - **phases / income / expenses** — gross salary, bonus and concessional super per person
     while working; living, rent and school/childcare costs per phase.
   - **retirement_spending.base** — the target annual retirement spend (today's money).
   - **events** — the years that matter: each person's retirement, super access, house
     purchase, inheritance, and the `horizon` (final) year (typically the horizon person's
     birth year + `longevity_age`).
   - **house** — the home's price in today's money (or delete the whole `house` block to
     model "rent forever").
   - **inheritance** — set `selected: zero` if none, else fill the `variants`.
3. **Cross-check coherence** as you go: confirm currency is consistent (one currency, AUD by
   convention); that the AU `tax` block matches their country (offer to adjust if not); and
   optionally set `meta.reconcile_target` to the sum of balances as a typo guard.
4. **Offer to run** `model/.venv/bin/python model/run.py --scenario recommended` once the
   mandatory fields are set, then help interpret the output (P(sustains), funded ratio,
   terminal P50) and explore scenarios.

Refer the user to `config.example.yaml` whenever they want to see a filled-in reference.

## Modelling rules (apply to every change here)

1. **One currency** in any single figure (AUD by convention). Convert to another currency
   only on demand, at the rate in `meta.fx`. Never mix currencies in one number.
2. **Net worth = everything** — cash, investments, pensions, super, all property, minus
   liabilities. Never project a partial slice as the total.
3. **Use a researched best-practice method** for the model type, and note the method used.
4. **Outputs are generated** — regenerate them; don't hand-edit `model/outputs/`.
5. **Don't restate generated numbers in prose docs.** Point to `model/outputs/` or the
   config. Keep the config the single source of truth.
6. **Tax/structure caveat:** confirm material tax and structure assumptions with a licensed
   adviser; the model is decision-support, not advice.

## Canonical sources (where each fact lives)

| For… | Go to |
|---|---|
| Your inputs (balances, income, expenses, events, assumptions) | `model/config/personal/config.yaml` |
| A complete worked example | `model/config/config.example.yaml` |
| "What if" overrides | `model/config/scenarios.yaml` |
| Projections, scenario results, funded ratio, MC probabilities | `model/outputs/` (run via `run.py`) |
| Why an assumption is set as it is | `model/DECISIONS.md` |
| Method & structure | `model/README.md` |
| Planning methodology research | `docs/research/` |
| Open work / future passes | `docs/plans.md` |
