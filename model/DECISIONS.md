# Model decision log

Dated, append-only record of the **assumptions and structural decisions** baked into
this model and *why* — so a future reader (or a future Claude) can see the reasoning,
not just the current `config.yaml` values. Newest entries first. Each entry lists the
evidence, the decision (including options weighed), what changed in code/config, the
resulting headline numbers, and any open items.

See also: `README.md` (method), `config/config.yaml` (the live values), `../docs/plans.md`
(open work).

This log starts empty for a new plan. Add an entry whenever you change a non-obvious
assumption (a return, an inflation rate, a tax treatment, a retirement date, a spending
strategy) so the "why" doesn't get lost.

---

## Template for a new entry

```
## YYYY-MM-DD — <short title of the decision>

**Evidence / trigger:** what prompted this (research, a source, a changed circumstance).

**Decision:** what you chose, and the options you weighed against it.

**Changed:** the exact config/code keys you edited (e.g. `assumptions.cma.equity.mean 0.07 -> 0.064`).

**Result:** the headline numbers before/after (P(sustains), funded ratio, terminal P50).

**Open items:** anything still to verify (flag tax/structure assumptions for a licensed adviser).
```
