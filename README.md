# AI-First Financial Planning Tool

An AI-assisted, config-driven **lifetime cash-flow model** for household financial planning.

The engine is a transparent Python model, your financial data lives in local config files,
and an LLM coding assistant makes it conversational. You answer questions in plain English;
the assistant fills the config, runs scenarios, and explains the results.

## It helps you meet your goals

The model tracks your asset values and cash flows over your whole life, so it can answer the questions that matter:

1. **I can't take much more — when can I afford to retire?** I want $X a month once I stop working — when do I get there?
2. **Will our money outlast us?** Do investments + pensions + super cover our retirement spend without the pot running dry?

## Then ask it anything

Your goals are just the start. Ask any "what if" you can dream up — seriously:

- *What happens to our net worth if I get married in two years and spend $25k on the wedding?*
- *If house prices dip this year and take three years to recover, when's the sweet spot to buy?*
- *Can I buy a $1M house and still not run out of money in retirement?*
- *When can I retire if I add $5k to my super every year?*
- *Can my husband stop working if we move to a cheaper rental that saves us $800/month?*

## Not financial advice
> ⚠️ **This tool is not financial advice.** It is a decision-support model for education and
> exploration. Outputs are projections from assumptions *you* control, not predictions or
> recommendations. Tax/structure defaults are illustrative (Australian by default).
> Confirm anything material with a licensed adviser. See [LICENSE](LICENSE).

## Quick start

This is built to be **driven by [Claude Code](https://claude.com/claude-code)** — you talk,
it does the work. You don't need to run commands or edit YAML by hand.

**Prerequisites:** Python 3.10+ and Claude Code. That's all.

1. **Get the project** — clone (or fork) this repo and open the folder in Claude Code (or run `claude` inside it).
2. **Say the word** — for example:

   > **"Let's start"** — or *"help me set up my plan"*, or just *"vamos!"*

   Say it however you like; Claude reads your intent, not magic words.

That's it. Claude then:

- **sets up the Python environment** (creates the venv, installs dependencies);
- **runs the fictional demo** so you can see what the model produces before you enter anything;
- **asks about your goals and finances** — when you want to retire, target spend, home
  vs. rent, balances — and writes your answers into your own **private, git-ignored** config;
- **runs your plan and explains the results**, then helps you explore "what if" scenarios.

The full flow Claude follows is in [CLAUDE.md](CLAUDE.md) — you don't need to read it. When the
first run finishes, head to **[Checking the results](#checking-the-results)**.

## Checking the results

When a run finishes, Claude talks you through it in plain English — but here's how to read
what comes back yourself.

**The headline line** — one row per scenario, printed to the console:

```
scenario                sustains  preserved  funded   P50 terminal
recommended                 83%       60%    1.42         5.75M
```

| Number | The question it answers | What to look for |
|---|---|---|
| **sustains** | Across thousands of simulated market histories, in how many is your spending met *every* year without the pool running dry? | Higher is safer — high-80s % and up is a common comfort target; well below that flags a real chance of falling short. |
| **preserved** | In how many does your capital end near where it started — i.e. you live off the returns, not the principal? | High if you want to leave a legacy or keep a buffer; low is fine if you mean to spend it down. |
| **funded** | The *funded ratio*: everything you have and will receive ÷ everything you plan to spend (both as present values). | **≥ 1.0** is fully funded. 1.42 ≈ 42% headroom. |
| **P50 terminal** | The median amount left at the very end, in today's money. | Comfortably above zero; the full P10–P90 spread is in the report. |

**The chart** (add `--chart`) — your whole financial life on one timeline: asset values on
top, the cash flowing in and out below.

![Sample assets & cash-flow chart from the fictional example](docs/assets/example-chart.png)

**The full report** — a markdown summary with the net-worth trajectory, the retirement-spend
glidepath, the complete Monte Carlo percentile spread, and every assumption used:
**[example-summary.md](docs/assets/example-summary.md)**.

Claude also prints an FCA-style **stress table** — which shocks (a year-one crash, a decade
of weak returns, high inflation, living longer) would deplete the pool, so you see the
failure modes and not just the rosy central case:

```
Stress overlays (deterministic central, terminal today's money):
  base                5.19M  ok
  year1_crash         2.80M  ok
  sustained_low       2.07M  DEPLETED
  high_inflation      1.44M  DEPLETED
  ...
```

For the full list of files each run produces, see [Outputs](#outputs).
*(All figures above are from the bundled fictional example — illustration only.)*

## How it works

Under the hood it's a recognised industry-standard method (a cash-flow forward simulator,
the approach used by Voyant / eMoney / RightCapital and expected by FCA FG22/5) with full
Australian-resident tax, per-bucket drawdown under super-access rules, a spending
glidepath, stress overlays, and an actuarial funded ratio.

### What's cool about this approach

It's **deterministic** — same inputs, same outputs, every time. No black box; just the
maths, laid out so you can check it.

And it's **agentic** — you don't edit spreadsheets or YAML, you just chat and tell it what
you want to explore.

---

## Using it

Once your plan is set up, you **just ask** — in plain English, in Claude Code. Claude
translates the question into a scenario, runs the model, and explains the result. You never
touch YAML or the command line for this. For example:

> *"Model me retiring at 50."*
> *"What happens if I retire at 60 and pay 20k toward my child's house deposit when I'm 53?"*
> *"Compare renting forever against buying in 2030."*
> *"How much worse is it if returns are 1% lower for my whole retirement?"*

Claude figures out which inputs to override, runs it, and tells you what changed — the
probability your money sustains, the funded ratio, terminal wealth (see
**[Checking the results](#checking-the-results)** for what those mean).

---

## Outputs

Every run writes to **`model/outputs/`** (git-ignored — these are generated, so regenerate
them rather than hand-editing). A single-scenario run lands at the top level; `--scenario all`
fans the per-scenario files into `model/outputs/scenarios/`. Each run produces:

| Artifact | What it is | Example |
|---|---|---|
| **`<scenario>-summary.md`** | A readable per-scenario report — headline P(sustains)/preserved/funded ratio, the net-worth trajectory, the retirement-spend glidepath, full Monte Carlo percentiles, and the documented assumptions. | [example-summary.md](docs/assets/example-summary.md) |
| **`<scenario>-chart.png`** | *(with `--chart`)* Two stacked panels sharing a timeline: **asset values** (net worth, investments, house, cash) on top and **annual cash flow** (saving/drawdown, housing, aged care) below, across your whole lifetime. | [example-chart.png](docs/assets/example-chart.png) |
| **`scenarios.xlsx`** | An Excel workbook: a **Summary** grid comparing every scenario, a **MonteCarlo** sheet, and a per-scenario **annual ledger** (assets → liabilities → net assets → inflows/outflows → net cash-flow → net worth, years as columns, in today's money). | — |

Also printed to the console: the one-line headline per scenario and an FCA-style **stress
table** (year-1 crash, sustained-low returns, high inflation, longevity tail, house
corrections, aged-care-from-pool) flagging which overlays deplete the pool.

The two files under [`docs/assets/`](docs/assets/) are committed snapshots of the fictional
example so you can preview the output here; your own runs never touch them.

---

## What's in here

```
README.md                  this file
CLAUDE.md                  project guide + the Claude onboarding flow (entry point for Claude)
LICENSE                    MIT + not-financial-advice disclaimer
model/                     the engine
  README.md                method, structure, and the full CLI reference
  run.py                   the CLI
  config/
    config.skeleton.yaml   the all-null template — copy into personal/ and fill in
    config.example.yaml    a complete fictional config you can run immediately
    scenarios.yaml         named "what if" overrides
    personal/              YOUR inputs live here (git-ignored); config.yaml is the default
  finmodel/                the model package (tax, returns, drawdown, Monte Carlo, …)
  tests/                   pytest suite (109 tests; run `.venv/bin/python -m pytest`)
  DECISIONS.md             dated log of why each assumption is what it is
docs/research/             planning-methodology research the model is built on
```

The tax defaults are Australian-resident; replace the `tax` block in your config to model
another country. The model deals in **one currency** (AUD by convention).

## Privacy

Your real data lives in `model/config/personal/`, which is **git-ignored as a whole** —
nothing you put there (your `config.yaml`, plan variants, exported numbers) is ever
committed. The tracked `config.skeleton.yaml` and `config.example.yaml` contain no real
data. If you fork this repo, a quick `git status` should never show anything under
`config/personal/` except its `README.md`.

The model and generated outputs run locally. If you use a hosted LLM, the prompts/context
you send to that LLM may leave your device, so treat those conversations as potentially
containing private financial information.

## Doing it by hand (optional)

You never *need* any of this — Claude does it all for you. But the model is a plain Python
CLI with plain-text config, so if you'd rather drive it yourself, you can.

**Set up and run:**

```bash
cd model
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# See the fictional demo immediately (no setup needed):
.venv/bin/python run.py --config config.example.yaml --scenario recommended

# Set up your own plan: copy the template into the git-ignored personal/ folder,
# fill in the fields marked `# FILL`, then run it:
cp config/config.skeleton.yaml config/personal/config.yaml
.venv/bin/python run.py --scenario recommended
```

| You want to… | Do this |
|---|---|
| Run the recommended plan | `run.py --scenario recommended` |
| Run every scenario at once | `run.py --scenario all` |
| Run one named scenario | `run.py --scenario rent_forever` |
| Add a chart (PNG) | add `--chart` |
| More Monte Carlo precision | add `--trials 5000` |
| Try the demo without setup | add `--config config.example.yaml` |

**Add a scenario by hand.** Scenarios are *sparse overrides* of your base config — change
only what differs. Add a block to
[`model/config/scenarios.yaml`](model/config/scenarios.yaml) and it becomes available to
`--scenario`. For example, "what if we retire a year earlier":

```yaml
  retire_early:
    events: { person1_retires: { year: 2052 } }
```

The shipped file has worked examples (cheaper house, no inheritance, rent forever, save
more, max super, …) to copy from. *(This is exactly the file Claude edits when you ask in
plain English — you're just doing it manually.)*

---

## License

[MIT](LICENSE), with a not-financial-advice disclaimer. Use at your own risk.
