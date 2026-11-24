# BACKEND_SCHEMA — The Fake Bitcoin Trap

There is no server and no database. The schema below is the **on-disk data
contract**; every module reads and writes exactly these shapes. Changing a
column is a breaking change and must update this file in the same commit.

## 1. `data/raw/BTCUSDT-1h-YYYY-MM.csv`

Headerless (some months carry a header, which the loader strips).

| Column | Type | Notes |
|---|---|---|
| open_time | int64 | epoch **ms**; **µs from 2025-01-01** (spot-only change) |
| open | float64 | |
| high | float64 | |
| low | float64 | |
| close | float64 | |
| volume | float64 | base asset |
| close_time | int64 | epoch ms |
| quote_volume | float64 | |
| trades | int64 | |
| taker_buy_base | float64 | |
| taker_buy_quote | float64 | |
| ignore | string | always `0`; present because the exchange ships it |

**Key:** `open_time` (after normalisation). **Constraint:** strictly increasing,
unique after de-duplication (`keep="last"`). **Rows dropped:** none.

## 2. `data/holdout/btcusdt_1h_holdout.parquet`

Same five columns as the in-memory frame: `open, high, low, close, volume`,
indexed by a UTC `DatetimeIndex`.

| Property | Value |
|---|---|
| Rows | last 365 days of the file, minus the final bar |
| Access | `btrap.data.load_holdout()` only, gated by env var |
| Audit | every successful read appends `ISO8601\tUSER` to `ACCESS_LOG.txt` |

## 3. `data/nulls/{A,B,C}.parquet`

One file per null family.

| Property | Value |
|---|---|
| Index | UTC `DatetimeIndex`, identical to the training frame |
| Columns | `{family}_{i:03d}` for i in 0..N_PATHS-1 |
| Values | log returns, float64 |
| Key | (index, column) |
| Invariant | each column is a complete path of the same length as training |

Family names are `A_gaussian_rw`, `B_block_bootstrap`, `C_garch_t`.

## 4. `data/trials/*.jsonl`

Append-only. One JSON object per backtest call, never edited in place.

| Field | Type | Meaning |
|---|---|---|
| `trial_id` | string(12) | random hex, unique per call |
| `agent_id` | string | which configuration/prompt |
| `tag` | string | free label (`ma_rule`, `holdout_single_read`, …) |
| `params` | object | strategy parameters |
| `code_hash` | string(16) | sha256 prefix of the strategy source |
| `sharpe_net` | float | annualised, after costs |
| `sharpe_gross` | float | before costs |
| `mean_net` | float | mean per-bar net return |
| `turnover` | float | sum of absolute position changes |
| `n_bars` | int | series length |
| `returns` | float[] | the net return series, rounded to 1e-10 |

**Constraints:**
- one line per call; a `trial_id` may appear once;
- correction protocol: append a new record containing
  `{"void": true, "refers_to": "<trial_id>"}`, never rewrite the original;
- `n_trials` used by the DSR is the line count of the file.

## 5. `outputs/deflation.json`

| Field | Type | Meaning |
|---|---|---|
| `best_trial` | string | trial_id of the declared winner |
| `best_params` | object | the parameters to replay on the holdout |
| `best_sharpe_annualised` | float | as reported by the agent/harness |
| `threshold_annualised_raw_n` | float | analytic E[max] at N = line count |
| `threshold_annualised_neff` | float | analytic E[max] at N_eff |
| `n_trials` | int | line count |
| `n_eff` | float | participation ratio |
| `dsr_raw_n` | float | PSR at the raw-N threshold |
| `dsr_neff` | float | PSR at the N_eff threshold — **the pass/fail number** |
| `passes` | bool | `dsr_neff >= 0.95` |
| `pbo` | float | probability of backtest overfitting |
| `pbo_splits` | int | number of CSCV splits used |

## 6. `outputs/neff_table.csv`

| Column | Meaning |
|---|---|
| `agent_id` | panel name (file stem) |
| `n_trials` | logged calls |
| `n_eff_participation_ratio` | (Σλ)²/Σλ² |
| `n_eff_onc_approx` | silhouette-optimal cluster count |
| `mean_pairwise_corr` | average off-diagonal correlation |
| `pca_top_fraction` | λ₁/Σλ |
| `best_sharpe` | max logged `sharpe_net` |

## 7. `outputs/holdout_result.json`

| Field | Meaning |
|---|---|
| `holdout_bars`, `holdout_start`, `holdout_end` | the sealed window |
| `params` | replayed parameters |
| `train_sharpe_annualised` | in-sample |
| `holdout_sharpe_annualised` | the honest number |
| `retention_ratio` | holdout / train |
| `dsr` | copied from `deflation.json` for the record |
| `passes_bar` | DSR ≥ 0.95 **and** retention ≥ 0.5 |

## 8. Access rules

| Path | Read | Write |
|---|---|---|
| `data/raw/` | anything | download script only |
| `data/holdout/` | `run_holdout.py` only | `seal_holdout.py` only |
| `data/trials/` | anything | `engine.TrialLog` only |
| `outputs/` | anything | pipeline stages only |
