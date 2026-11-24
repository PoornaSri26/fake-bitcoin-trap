# ARCHITECTURE — The Fake Bitcoin Trap

## 1. System overview

```
              data.binance.vision
                      |
                      v
   scripts/download_data.py  -->  data/raw/*.csv
                      |                    |
                      |                    +--> scripts/seal_holdout.py --> data/holdout/ (sealed)
                      v
            btrap.data.load_train()
                      |
                      v
              btrap.nulls  -->  data/nulls/{A,B,C}.parquet
                      |
                      v
   reference agent or LLM agent
                      |
            btrap.engine.run()  --appends-->  data/trials/*.jsonl
                      |
        +-------------+-------------+
        v                           v
   btrap.neff                  btrap.dsr, btrap.cscv
        |                           |
        +-------------+-------------+
                      v
               outputs/deflation.json
                      |
                      v
          btrap.pipeline.stage_charts
                      |
                      v
             outputs/figures/*.png

   [sealed] data/holdout --> scripts/run_holdout.py --> outputs/holdout_result.json
```

## 2. Layers and responsibilities

| Layer | Module | Responsibility | Must never |
|---|---|---|---|
| Ingestion | `data.py`, `scripts/download_data.py` | bytes → clean frame | compute statistics |
| Simulation | `nulls.py` | synthetic paths | touch real returns beyond moments |
| Execution | `engine.py` | positions → net returns, logging | decide what a strategy is |
| Strategy | `ma_rules.py`, `agents.py` | propose positions | read files |
| Inference | `neff.py`, `dsr.py`, `cscv.py` | selection-bias maths | read raw data |
| Orchestration | `pipeline.py` | stage wiring | contain formulas |
| Reporting | `stage_charts`, `README.md` | figures and prose | add new statistics |

## 3. Data flow: one trial

1. `pipeline.stage_trials` loads returns (train only) via `data.load_train`.
2. It constructs a `TrialLog` with a hard call budget.
3. `ReferenceAgent.explore` enumerates rules; each calls `engine.run`.
4. `engine.run` computes positions, applies the one-bar lag, charges turnover,
   hashes the strategy source, appends a JSONL record, and returns a summary.
5. `stage_neff` stacks the logged return series into a T×N matrix and estimates
   N_eff.
6. `stage_dsr` deflates the max-Sharpe trial and writes one JSON document.
7. `stage_charts` renders two figures. No statistics are computed here.

## 4. Folder structure

```
01-fake-bitcoin-trap/
├── docs/                  the 12 project documents
├── AGENTS.md              agent operating manual
├── README.md              question, bar, result
├── PREREGISTRATION.md     the frozen bar (+ .sha256)
├── Makefile               the single reproduce entry point
├── reproduce.sh/.ps1      shims for machines without make
├── requirements.txt
├── data/                  gitignored except README
│   ├── raw/  holdout/  nulls/  trials/
├── src/btrap/
│   ├── config.py  data.py  nulls.py  engine.py  ma_rules.py
│   ├── agents.py  neff.py  dsr.py  cscv.py  pipeline.py  plotting.py
├── scripts/
│   ├── download_data.py  seal_holdout.py  stamp_prereg.py  run_holdout.py
├── tests/
└── outputs/               figures + json (gitignored)
```

## 5. Architectural decisions

| Decision | Why | Consequence |
|---|---|---|
| Trial count from the harness, not the transcript | the transcript is a summary; the log is the evidence | an agent cannot under-report by omission |
| One narrow `engine.run` signature | limits what a strategy can see | no multi-asset or portfolio strategies in v1 |
| Holdout outside the working tree | "remember not to peek" is not a control | one extra CLI step, and a log file |
| JSONL for trials | append-only, greppable, crash-safe | large files (120 trials × 8.7k bars ≈ 30 MB) |
| Parquet for null panels | one file per family, columnar, fast | needs pyarrow |
| Seeds derived as `(seed, path_index, family)` | resumable and non-overlapping | changing `N_PATHS` keeps earlier paths identical |
| Formulas in docstrings above implementations | the project's whole claim is that the maths is derivable | more prose in code than usual |
| `AgentProfile.prompt` lives in `config.py` | the prompts are an experimental variable | editing them is a re-registration |

## 6. Where a new agent plugs in

`agents.LLMAgentAdapter` is the only integration surface: give it a `data_root`
that excludes `data/holdout`, a log path, and a budget. The agent's tools must
expose `propose(...)`, which calls `engine.run`. Nothing else in the codebase
needs to change, and no other module may be given filesystem access.
