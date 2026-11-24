# TRD — The Fake Bitcoin Trap

## 1. Project overview

| Item | Value |
|---|---|
| Name | `btrap` |
| Language | Python 3.11+ (verified on 3.13.5) |
| Core stack | numpy, pandas, scipy, matplotlib, pyarrow |
| Optional | `arch` (GARCH-t null); falls back to a moment-matched simulation |
| Storage | Parquet (nulls) + JSONL (trials) + JSON (results) |
| Compute | single CPU, ~2 GB RAM for the default sizes |
| Hosting | none — runs locally |

## 2. Technical objectives

- **Reproducible:** fixed seeds, no wall-clock dependence in any statistic.
- **Auditable:** every number in the output can be traced to a log line.
- **Bounded:** memory and runtime known in advance so the grid can be resized.
- **Honest by construction:** the holdout cannot be opened by accident.

## 3. Functional requirements

| ID | Requirement |
|---|---|
| F1 | Download spot 1h klines by month, verify `.CHECKSUM`, handle headerless/headed CSVs |
| F2 | Normalise timestamps across the 2025-01-01 spot switch to microseconds |
| F3 | Split train/holdout at a fixed boundary (48 / 12 months) |
| F4 | Generate null paths for three families, seeded per path |
| F5 | Backtest with one-bar execution lag and per-unit-turnover costs |
| F6 | Log each trial with params, code hash, return series |
| F7 | Estimate N_eff two ways |
| F8 | Compute PSR, expected max Sharpe, DSR, PBO |
| F9 | Emit the two required charts |
| F10 | Provide a one-shot holdout evaluator |

## 4. Non-functional requirements

| Requirement | Target |
|---|---|
| Reproduce runtime | < 30 min on 4 CPU cores at default sizes |
| Peak memory | < 2 GB |
| Determinism | identical outputs for identical seeds on the same machine |
| Portability | Linux/macOS with `make`, Windows with `reproduce.ps1` |
| Dependency footprint | ≤ 8 direct dependencies |
| Failure mode | missing data → explicit error naming the command to run |

## 5. Technology stack and responsibility

| Layer | Technology | Responsibility |
|---|---|---|
| Numerics | numpy | arrays, RNG, eigendecomposition |
| Frames | pandas | time-indexed returns, joins |
| Statistics | scipy.stats | normal/quantile functions, skew/kurtosis |
| Storage | pyarrow/parquet | null panels, dense numeric matrices |
| Logging | stdlib json | append-only trial log |
| Charts | matplotlib (Agg) | the two deliverable figures |
| Tests | pytest | the invariants in `docs/TESTING.md` |
| Optional | arch | GARCH(1,1)-t fitting |

**Rejected deliberately:** vectorbt (keeps the engine honest and dependency-free;
a cross-check is listed as follow-up), polars (no benefit at these sizes),
jupyter (a notebook is not a reproducible artefact).

## 6. Integrations

| Service | Endpoint | Auth | Notes |
|---|---|---|---|
| Binance public data | `data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/` | none | checksums published alongside; **spot timestamps switch to µs from 2025-01-01** |

No other network calls. No API keys are required or accepted by this project.

## 7. Constraints and assumptions

- Spot only; no funding, no shorting constraints modelled.
- Fixed 5 bp fee + 2 bp slippage per side. This is a modelling choice and is
  frozen in the pre-registration; changing it is a re-registration.
- Returns are log returns from close to close; no intrabar path.
- The null worlds are simulators. GARCH-t understates regime breaks, and the
  block bootstrap can preserve structure that a real trend detector would find.
  Both limitations are stated in the report rather than hidden.
- One machine, one seed family, one instrument: the result is about *this*
  setup and is not a general claim about agents.
