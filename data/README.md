# data/

Nothing here is committed except this file. Layout:

```
data/raw/          BTCUSDT-1h-YYYY-MM.csv  (from data.binance.vision)
data/holdout/      btcusdt_1h_holdout.parquet + ACCESS_LOG.txt
data/nulls/        null_A.parquet, null_B.parquet, null_C.parquet + manifest.json
data/trials/       one JSONL per agent panel: every backtest call, in order
```

## Rules

- `data/holdout/` is **not** mounted into the agent sandbox. If it is visible to
  the agent, the experiment is void — say so, do not quietly delete the finding.
- `data/trials/*.jsonl` is append-only evidence. Never edit a line; if a trial
  was mis-logged, add a `"void": true` field in a *new* record referencing it.
- Re-downloading data should reproduce the same files; checksums are verified
  against the `.CHECKSUM` files published alongside each archive.

## Size

60 months of 1h spot klines ≈ 90 MB. The futures `bookTicker` archives used by
project 2 are far larger (3–8 GB per month) — see that project's README.
