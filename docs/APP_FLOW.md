# APP_FLOW — The Fake Bitcoin Trap

There is no UI. The "screens" are CLI stages, and the "user journey" is the
order in which a researcher must run them. This file exists so an agent does not
invent stages or reorder them.

## 1. Stage list

| Stage | Command | Reads | Writes |
|---|---|---|---|
| 0. Register | `make stamp` | `PREREGISTRATION.md` | `PREREGISTRATION.sha256` |
| 1. Acquire | `make data` | network | `data/raw/*.csv`, `data/holdout/*.parquet` |
| 2. Nulls | `make nulls` | `data/raw` | `data/nulls/*.parquet` |
| 3. Trials | `make trials` | `data/nulls` | `data/trials/*.jsonl` |
| 4. N_eff | `make neff` | `data/trials/real.jsonl` | `outputs/neff_table.csv` |
| 5. Deflate | `make dsr` | trials | `outputs/deflation.json` |
| 6. Charts | `make charts` | outputs | `outputs/figures/*.png` |
| 7. Holdout | `make holdout` | sealed | `outputs/holdout_result.json` |

## 2. Main journey

```
stamp → data → nulls → trials → neff → dsr → charts → [holdout, once]
```

The ordering is not cosmetic:

- **stamp before data**, because a bar written after seeing the data is not a
  bar.
- **nulls before trials**, because the null panel defines what the agent is
  scored against.
- **charts before holdout**, because a chart drawn after the holdout read is a
  report, not a pre-registered analysis.

## 3. Per-stage detail

### Stage 1 — Acquire
- **Sees:** a month-by-month progress line and a final `58/60 months present`.
- **Actions:** retry a month by re-running; `--force` re-downloads.
- **Empty state:** `no klines in data/raw. Run: python scripts/download_data.py --months 60`.
- **Partial success:** exit code 1 with the failing months listed. The pipeline
  will still run on what is present, and the boundary moves — that is a
  re-registration and the script says so.

### Stage 3 — Trials
- **Sees:** one line per agent panel searched.
- **Actions:** rerun after editing `config.AGENTS` prompts.
- **Budget state:** when `max_calls` is hit, `engine.run` raises
  `RuntimeError: budget exhausted` and `ReferenceAgent.explore` stops cleanly.
  It does **not** silently keep going.

### Stage 5 — Deflate
- **Success:** prints JSON with `dsr_neff`, `n_eff`, `pbo`, `passes`.
- **Failure (expected, and fine):** `passes: false`. This is a result.

### Stage 7 — Holdout
- **Guard:** refuses to run if `outputs/holdout_result.json` exists.
- **Refuses** if `make dsr` has not produced a declared winner.
- **Logs** the read to `data/holdout/ACCESS_LOG.txt` before returning data.

## 4. States

| State | Meaning | Where it shows |
|---|---|---|
| Loading | download or null generation running | stdout progress lines |
| Empty | no data / no trials | explicit error naming the fixing command |
| Success | stage wrote its artefact | one summary line + exit 0 |
| Error | checksum mismatch, 429, shape mismatch | stderr, exit non-zero |
| Sealed | holdout present but locked | `HoldoutAccessError` with instructions |

## 5. Edge cases

| Case | Behaviour |
|---|---|
| A month file has a header row | stripped by `data._read_klines` |
| A month file is missing | month skipped; boundary unchanged; exit 1 |
| Timestamps in ms and µs mixed | normalised by magnitude in `_read_klines` |
| Fewer than 3 trials logged | `neff` and `dsr` skip that panel with a message |
| Trial series of unequal length | `trial_matrix` trims to the common length |
| `arch` not installed | GARCH-t falls back to a hand-rolled t-GARCH |
| Holdout read twice | refused unless `BTRAP_ALLOW_REPEAT=1` |

## 6. Access rules

| Artefact | Who may read it |
|---|---|
| `data/raw/`, `data/nulls/` | anything, including the agent |
| `data/trials/` | the harness writes; humans read |
| `data/holdout/` | **only** `scripts/run_holdout.py`; never the agent sandbox |
| `PREREGISTRATION.sha256` | anyone; it is the tamper evidence |
