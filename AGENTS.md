# AGENTS.md — The Fake Bitcoin Trap

## Project

A research instrument that counts every strategy an AI agent tries on BTC data
and deflates its best Sharpe for that search. Python 3.11+, numpy/pandas/scipy,
no server, no database, no deployment.

## Commands

```bash
pip install -r requirements.txt
make stamp          # timestamp + hash PREREGISTRATION.md, then commit
make data           # 90 MB of 1h klines, checksum-verified
make reproduce      # nulls -> trials -> neff -> dsr -> charts (never the holdout)
make test           # pytest -q tests
make holdout        # ONE-SHOT sealed read; requires explicit authorisation
```

Windows without `make`: `bash reproduce.sh` or `pwsh reproduce.ps1`.
All Python entry points need `PYTHONPATH=src`.

## Documentation map

| Question | File |
|---|---|
| What are we building and why? | `docs/PRD.md` |
| Which stack, which endpoints? | `docs/TRD.md` |
| What runs in what order? | `docs/APP_FLOW.md` |
| How is the code organised? | `docs/ARCHITECTURE.md` |
| What are the on-disk shapes? | `docs/BACKEND_SCHEMA.md` |
| How should figures look? | `docs/DESIGN_SYSTEM.md` |
| Naming, docstrings, commits | `docs/CODE_STYLE.md` |
| What to build next | `docs/IMPLEMENTATION_PLAN.md` |
| Secrets and integrity controls | `docs/SECURITY.md` |
| What must be tested | `docs/TESTING.md` |
| **The pass/fail bar** | `PREREGISTRATION.md` |

## Rules — Always

1. Read `docs/` before changing anything, starting with `PRD.md` and `ARCHITECTURE.md`.
2. Every statistic keeps its formula in the docstring above the implementation.
3. `PYTHONPATH=src python -m pytest -q tests` must pass before you say "done".
4. Seeds come from `config.SEED` via `np.random.default_rng`.
5. Only `config.py` holds experiment constants. Never hard-code 0.95 or 5 bp.
6. Update `docs/BACKEND_SCHEMA.md` in the same commit as any schema change.
7. Keep `make reproduce` green. It must never touch the holdout.

## Rules — Ask first

- Editing `PREREGISTRATION.md` (needs a `RE-REGISTER` commit explaining why).
- Adding a dependency.
- Changing costs, the train/holdout split, or the agent prompts.
- Running `make holdout`.
- Deleting or rewriting a line in `data/trials/*.jsonl`.

## Rules — Never

- Read, copy, or symlink `data/holdout/` from anything but `scripts/run_holdout.py`.
- Commit data, outputs, or `.env`.
- Edit a logged trial in place (append a `{"void": true}` record instead).
- Insert a `shift(-1)` anywhere in a feature or a strategy.
- Report a Sharpe without its trial count.
- Describe a `Pending` row in `docs/TESTING.md` as passing.
- Claim a speedup or an edge without a measurement in the repo.

## Definition of done

A change is done when: tests pass, `make reproduce` runs to completion, the
affected docs are updated, and no number in the README contradicts
`outputs/deflation.json`.

Generating code is not completing a task.
