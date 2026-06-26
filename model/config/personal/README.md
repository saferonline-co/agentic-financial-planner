# Your private plan lives here

Everything in this folder is **git-ignored** (except this README) — it is the safe
home for files that contain your real financial data, so they are never committed.

The model reads **`config.yaml`** from this folder by default. Create it by copying
the tracked, all-null template:

```bash
cp ../config.skeleton.yaml config.yaml      # run from model/config/personal/
# …or from the model/ directory:
cp config/config.skeleton.yaml config/personal/config.yaml
```

Then fill it in (the fields marked `# FILL` are mandatory) — or open the project in
Claude Code and say **"help me set up my plan"** and it will do this for you.

Anything else personal (alternative plan variants, exported numbers, notes) can also
live here and will stay out of git automatically.
