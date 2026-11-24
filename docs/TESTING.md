# TESTING — The Fake Bitcoin Trap

## 1. Overview

| Type | What it checks | Tool |
|---|---|---|
| Unit | the statistics against closed-form limits | pytest |
| Property | invariants that must hold for any input (lag, turnover, monotonicity) | pytest |
| Integration | one stage writes the artefact the next stage reads | pytest + tmp_path |
| Reproducibility | two runs with the same seed produce byte-identical output | shell |
| Not automated | visual quality of the two figures | human |

## 2. Goals

1. A bug in the cost model must fail a test, not quietly raise Sharpe.
2. Look-ahead in a strategy must fail a test.
3. The holdout must be unreachable without the env var.
4. N_eff must return the known answer on synthetic data with known correlation.

## 3. Key flows that must not break

- `download → seal → split → nulls → trials → neff → dsr → charts`.
- `deflation.json → run_holdout.py → holdout_result.json`, exactly once.

## 4. Test cases

| ID | Scenario | Expected | Type | Status |
|---|---|---|---|---|
| TC-01 | PSR of a mean-centred series | exactly 0.5 | unit | Pass |
| TC-02 | PSR under the null, 300-bar samples | mean in (0.35, 0.65), never ~1 | unit | Pass |
| TC-03 | PSR increases with added drift | monotone | unit | Pass |
| TC-04 | Expected max Sharpe vs 400k Monte-Carlo draws, N=120 | within 5% | unit | Pass |
| TC-05 | DSR at N=10 vs N=5000 on the same winner | strictly lower at 5000 | unit | Pass |
| TC-06 | Cost model on 1→1→-1→-1 positions | net = −3 × 7 bp | unit | Pass |
| TC-07 | Participation ratio of 20 independent series | ≈ 20 (±3) | unit | Pass |
| TC-08 | Participation ratio of 10 copies of one series | < 1.2 | unit | Pass |
| TC-09 | Sharpe of a constant series | 0.0 | unit | Pass |
| TC-10 | `load_holdout()` without the env var | raises `HoldoutAccessError` | unit | **Pending** |
| TC-11 | `engine.run` beyond `max_calls` | raises `RuntimeError` | unit | **Pending** |
| TC-12 | Two runs, same seed, `nulls` stage | identical parquet checksums | reproduc. | **Pending** |
| TC-13 | MA universe generated | 959 rules, else raises | unit | **Pending** |
| TC-14 | Trial count in `deflation.json` equals JSONL line count | equal | integration | **Pending** |
| TC-15 | Injected look-ahead (`shift(-1)` in a strategy) | holdout Sharpe collapses | manual | **Pending** |

A `Pending` row is not a pass. Nothing in `docs/` may be described as verified
until its row says Pass.

## 5. Running

```bash
make test                       # pytest -q tests
PYTHONPATH=src python -m pytest -q tests -k dsr
bash reproduce.sh nulls trials  # stage-level integration
```

## 6. Testing checklist

- [ ] Tests run without network access.
- [ ] Tests do not write into `data/` (use `tmp_path`).
- [ ] No test depends on the holdout existing.
- [ ] Every statistic module has at least one closed-form check.
- [ ] The cost model test would fail if turnover costs were dropped.

## 7. What is *not* tested (and why)

- **The agent's behaviour.** It is an LLM; behaviour is the object of study, not
  a unit under test. The harness around it is tested instead.
- **The figures.** Rendered by eye against `DESIGN_SYSTEM.md`.
- **PnL realism.** There is no order-book simulation; the cost model is a
  deliberate simplification, stated in `docs/TRD.md`.
- **Multiple machines.** Determinism is claimed per machine and seed only.
