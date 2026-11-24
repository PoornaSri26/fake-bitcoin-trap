# IMPLEMENTATION_PLAN — The Fake Bitcoin Trap

**Objective:** a runnable instrument in two weeks of part-time work, with the
bar frozen before any data is touched.
**Team:** one person. **Approach:** phases that each end in a testable artefact.

## Phase 0 — Freeze (day 1)

| Task | Deliverable | Done when |
|---|---|---|
| Write the bar | `PREREGISTRATION.md` | every constant in the config table has a value and a reason |
| Stamp and commit | `PREREGISTRATION.sha256` | `git log` shows `Freeze pre-registration` as the first code-touching commit |
| Skeleton | repo layout, Makefile, requirements | `make help` works |

**Gate:** nothing in `src/` is written before this phase is committed.

## Phase 1 — Data (days 2-3)

| Task | Deliverable |
|---|---|
| Downloader with checksum verify | `scripts/download_data.py` |
| Timestamp normalisation (ms vs µs) | `btrap.data._read_klines` |
| Split + seal | `scripts/seal_holdout.py` + `load_holdout` guard |
| Unit tests for label/split invariants | `tests/` |

**Gate:** `make data` produces 60 files, `data/holdout/` exists, and
`load_holdout()` raises without the env var.

## Phase 2 — The instrument (days 4-6)

| Task | Deliverable |
|---|---|
| Backtest with lag + turnover costs | `btrap.engine` |
| Append-only trial log | `data/trials/*.jsonl` |
| 959-rule universe with a self-check | `btrap.ma_rules` |
| Reference agent (no LLM needed) | `btrap.agents.ReferenceAgent` |

**Gate:** a deliberate double-counting bug (e.g. forgetting the lag) makes the
Sharpe jump, and the test catches it. Verify this by introducing it on a branch.

## Phase 3 — Nulls (days 7-8)

| Task | Deliverable |
|---|---|
| Three null families | `btrap.nulls` |
| Seeded, resumable generation | `data/nulls/*.parquet` |
| Empirical best-of-N distribution | Chart 1 |

**Gate:** empirical p95 and analytic E[max] agree within 10% at N=120. If they
do not, the harness is wrong and nothing downstream counts.

## Phase 4 — Deflation (days 9-11)

| Task | Deliverable |
|---|---|
| PSR/DSR with skew and kurtosis | `btrap.dsr` |
| N_eff two ways | `btrap.neff` |
| PBO/CSCV | `btrap.cscv` |
| N_eff validated on the 959-rule universe | a row in `neff_table.csv` |

**Gate:** on synthetic trials with known correlation (k independent blocks
duplicated m times), the participation ratio returns ≈ k. Add it as a test.

## Phase 5 — Run the experiment (days 12-13)

| Task | Deliverable |
|---|---|
| Three agent configurations on real data + null paths | `data/trials/` |
| Charts 1 and 2 | `outputs/figures/` |
| `neff_table.csv` per agent | `outputs/` |

**Gate:** the trial count per configuration is ≥ 200 and matches the log length.

## Phase 6 — Holdout and write-up (day 14)

| Task | Deliverable |
|---|---|
| Single holdout read | `outputs/holdout_result.json` |
| README result line, as-is | one sentence at the top |
| Interview prep re-derived on paper | `docs/` untouched, checked by hand |

**Gate:** the README's first ten lines contain the question, the bar and the
result. No hedging, no "promising".

## Post-launch (optional, only if asked)

- Cross-check the engine against vectorbt on 20 trials.
- Add a "report only your best" agent to measure the reporting gap.
- Repeat at daily frequency to show the deflation penalty is
  frequency-independent after annualisation.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Nulls accidentally easier than reality | three families; report the hardest |
| Agent sandbox can see the holdout | mount check, plus a test that the path is absent |
| N_eff disagreement embarrasses the result | report both, state which is used for the bar |
| Two weeks slip into four | the bar is already frozen; stop adding and report what ran |
