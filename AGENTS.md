# Agent Instructions

This repository is an AI-assisted financial planning tool.

Primary project guide: [CLAUDE.md](CLAUDE.md)

Agents should read `CLAUDE.md` before making changes or onboarding a user. It contains:

- project purpose and modelling rules
- first-run onboarding flow
- config locations and privacy rules
- run/test commands
- source-of-truth guidance

Key reminders:

- User financial data belongs only in `model/config/personal/`, which is git-ignored.
- Generated outputs belong in `model/outputs/`; regenerate them, do not hand-edit.
- This tool is decision-support only, not financial advice.
