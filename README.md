# The Fake Bitcoin Trap

**Question.** How many strategies does an AI agent silently try, and how much of
its best real-data Sharpe survives once you charge for those tries?

**Bar.** DSR ≥ 0.95 on the agent's single declared winner, *and* sealed-holdout
Sharpe ≥ 0.5 × training Sharpe. Frozen in `PREREGISTRATION.md` before any data
was touched. See `PREREGISTRATION.sha256`.

**Result.** _Not yet run._ This repository is the instrument, not the finding.
Fill this line in only after `scripts/run_holdout.py` has been executed once.

---

## Why this project first

It is the most self-contained of the five: one instrument, one file format, one
download. The statistical content (selection bias under a known number of
trials) transfers to every other project and to every interview.

## Documentation

Maintained per `AGENTS.md`; the twelve documents live in `docs/`:
`PRD` (scope, bar) · `TRD` (stack, the one endpoint) · `APP_FLOW` (stage order,
sealed-holdout states) · `ARCHITECTURE` (module boundaries) · `BACKEND_SCHEMA`
(CSV/JSONL/JSON shapes) · `DESIGN_SYSTEM` (the two charts) · `CODE_STYLE`
(the formula-in-docstring rule) · `IMPLEMENTATION_PLAN` (two weeks) · `SECURITY`
(integrity controls) · `TESTING` (cases + statuses).
The frozen bar is `PREREGISTRATION.md`, hashed to `PREREGISTRATION.sha256` by
`make stamp`.

## Layout

```
docs/                   the 12 project documents
AGENTS.md               agent operating manual
PREREGISTRATION.md      the bar, frozen and hashed
data/                   downloaded klines + null paths (gitignored)
  holdout/              ONLY read by scripts/run_holdout.py
src/btrap/
  data.py               kline loading, truncation, holdout sealing
  engine.py             numpy backtest + the trial logger (the instrument)
  ma_rules.py           the 959 moving-average rules (calibration universe)
  nulls.py              Gaussian RW, block bootstrap, GARCH(1,1)-t
  neff.py               participation ratio + ONC clustering
  dsr.py                PSR / DSR, expected max Sharpe
  cscv.py               probability of backtest overfitting
  pipeline.py           stages 1-6, wired together
scripts/
  download_data.py      klines from data.binance.vision
  stamp_prereg.py       timestamps + hashes the bar
  run_holdout.py        the single holdout read
  null_calibration.py   Chart 1
docs/
  interview_prep.md     the derivations to be able to do on a whiteboard
```

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make stamp        # timestamp + hash the pre-registration, then commit
make data         # ~90 MB of 1h klines, checksum-verified
make reproduce    # nulls -> agent trials -> N_eff -> DSR -> charts
```

`make reproduce` is deterministic given `--seed 7`. It does **not** touch the
holdout. `make holdout` is a separate, once-only target.

## The four things that make this honest

1. **The trial count comes from the harness, not the transcript.** `engine.run`
   appends one JSONL record per call: params, code hash, resulting return
   series. An agent that runs a strategy and never mentions it is still charged.
2. **The holdout is not in the room.** `data.holdout_path()` resolves outside
   `data/`'s working tree and refuses to open unless `BTRAP_RELEASE_HOLDOUT=1`.
   The agent sandbox is a Docker mount that excludes that directory.
3. **Nulls are calibrated, not asserted.** The threshold is the empirical
   distribution of "best Sharpe on noise", compared against the analytic
   expected maximum.
4. **Costs are charged on every turn of position**, not on a round trip.

## Expected outcome

At 120 trials of hourly noise, the expected maximum Sharpe is large enough that
most agents will report a training Sharpe near or below the noise threshold. The
interesting output is the *gap* between what the agent says it found and what
the nulls say it could have found by luck — and how that gap widens with the number
of unmentioned trials.

## What I'd do next

- Swap the numpy engine for vectorbt on a sample of trials to confirm the
  cost accounting matches, and report any divergence.
- Add a fourth agent configuration with an explicit "say only your best
  result" instruction, to measure the reporting gap directly.
- Repeat at 5m and daily frequency: if the deflation penalty is
  frequency-independent after annualisation, the harness is behaving.

## Attribution

Scaffold generated with an AI coding agent. Every equation in `dsr.py`,
`neff.py` and `cscv.py` is written out in the docstring immediately above its
implementation so it can be re-derived and checked by hand.
