# Pre-registration — The Fake Bitcoin Trap

**Registered at (UTC):** `2026-11-24T16:42:22Z`
**Frozen bar hash:** see `PREREGISTRATION.sha256` (written by `make stamp`)

Editing this file after it is stamped requires a new commit that says `RE-REGISTER`
and a paragraph explaining what changed and why. Bars may be sharpened, never
loosened.

## The question

How many strategies does an AI agent silently try, and how much of its best
real-data Sharpe is left once you charge for those tries?

## Fixed quantities (set before seeing any result)

| Quantity | Value | Why this value |
|---|---|---|
| Instrument | BTCUSDT spot, 1h klines | one series, no universe-selection degree of freedom |
| Source | `data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/` | free, versioned, checksummed |
| Training window | first 48 months of the file | long enough for a null distribution |
| Sealed holdout | final 12 months | read exactly once, by `scripts/run_holdout.py`, never inside the agent sandbox |
| Costs | 5 bp fee + 2 bp slippage per side | taker on Binance spot plus a conservative slippage |
| Agent configurations | 3 (A: terse, B: thorough, C: adversarial/self-critical) | the variable under study |
| Budget per run | 120 backtest calls, hard cap enforced by the harness | "budget" must be countable, not vibes |
| Null paths | 200 per null family | resolution of the 99th percentile |
| Null families | A Gaussian RW, B block bootstrap (block=24), C GARCH(1,1)-t | C is the trap inside the trap |
| N_eff estimators | (a) PCA participation ratio, (b) ONC cluster count | two independent ways, both reported |
| DSR threshold | 0.95 | the stated pass/fail line |

## Pass / fail bar (the only one)

An agent "found real structure" if and only if **both** hold:

1. **DSR ≥ 0.95** on its single declared winner, using N_eff from the
   *logged* trial count and the realised variance of trial Sharpes, and
2. the winner's **sealed-holdout Sharpe ≥ 0.5 × its training Sharpe**, with the
   holdout read once.

Additionally, as a *calibration* result (not a pass/fail): the reported best
Sharpe on null data must fall inside the empirical Monte-Carlo band for
"N trials of noise" at least 90% of the time. If it does not, the harness —
not the agent — is broken and no claim is made.

## What would make this fail outright

- Fewer than 200 logged backtest calls per configuration on real data: the
  trial count is under-observed and the experiment is void.
- Any read of the holdout file from inside `src/` or the agent sandbox: the
  experiment is void, not just the result.
- Holdout present in the agent's working directory at run time: void.

## What is explicitly *not* claimed

That the article's numbers hold. The 82% imbalance result, the 59% trade-match
rate and the "13 effective trials" are treated as hypotheses with unknown
provenance. Nothing here depends on them.

## Reporting rule

The null result is a reportable result. "The textbook effect does not survive
deflation at 120 trials" is the expected outcome and will be written up as
such, with the null calibration curve as Chart 1.
