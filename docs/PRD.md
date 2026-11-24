# PRD — The Fake Bitcoin Trap

## 1. Overview

A reproducible experiment that measures how many strategies an AI agent
actually tries on BTC data, and how much of its best Sharpe survives a
correction for that search.

It is a **research instrument**, not a product. The deliverable is a defensible
number, a null-calibration chart, and a write-up that can be defended in an
interview.

## 2. Problem statement

An agent that is asked to "find a profitable strategy" will try dozens of
variants and report the best one. The reported Sharpe is a maximum over trials,
so it is biased upward by an amount that grows with the number of tries. The
agent usually reports only the winner, so the reader cannot correct for it.

Two failure modes follow:

- **Overclaiming:** a Sharpe of 2.0 on noise gets presented as alpha.
- **Underclaiming:** a real effect is dismissed because nobody knows what the
  noise threshold actually was.

Nobody can fix either without *counting the trials* and *calibrating the null*.

## 3. Goals (measurable)

| # | Goal | Measure |
|---|---|---|
| G1 | Count every strategy the agent runs | ≥ 200 logged backtest calls per configuration, from the harness, not the transcript |
| G2 | Know what "best on noise" looks like | 200 null paths per family; empirical p95 of best Sharpe within 10% of the analytic Gumbel value |
| G3 | Deflate honestly | DSR computed with skew/kurtosis, with raw N and N_eff both reported |
| G4 | One-shot holdout | exactly one holdout read, logged with a timestamp |
| G5 | One command | `make reproduce` (or `reproduce.ps1` on Windows) runs stages 1-6 with no manual steps |

## 4. Target users

- **Primary:** the author, using it as a portfolio project and interview
  artefact. The reader is a quant researcher who will try to break it.
- **Secondary:** anyone who wants a template for selection-bias accounting on a
  single instrument.

## 5. Features and priorities

| Priority | Feature |
|---|---|
| Must | Kline download with checksum verification |
| Must | Sealed holdout, unreachable from the sandbox by construction |
| Must | Backtest engine with fixed costs and a per-call JSONL trial log |
| Must | Three null families (Gaussian RW, block bootstrap, GARCH-t) |
| Must | N_eff by two methods (participation ratio, ONC-approx) |
| Must | DSR with skew/kurtosis, CSCV/PBO, one-shot holdout |
| Must | Chart 1 (best-on-null vs N) and Chart 2 (reported vs deflated) |
| Should | Three agent configurations, incl. an adversarial/self-critical one |
| Should | Validation of N_eff on the 959-rule universe where the answer is known |
| Could | Extra frequency (daily, 5m) as a robustness row |
| Could | A "report only your best" agent to measure the reporting gap |
| Won't | Any live trading, paper trading or order routing |
| Won't | Any hosted service, dashboard or database |
| Won't | A claim about the article's 82% / 59% / 13-trial figures |

## 6. User stories

**US-1** — *As the researcher, I want the trial count to come from the harness
so that an agent cannot under-report.*
Acceptance: `data/trials/real.jsonl` has one line per `engine.run` call; its
line count equals the DSR's `n_trials`; deleting a line breaks a test.

**US-2** — *As the researcher, I want the holdout to be physically absent from
the sandbox so that accidental leakage is impossible.*
Acceptance: `btrap.data.load_holdout()` raises unless
`BTRAP_RELEASE_HOLDOUT=1`, and `data/holdout/` is excluded from the sandbox
mount; a test asserts the exception.

**US-3** — *As a reader, I want to know what luck alone produces at my trial
count so I can judge the reported Sharpe.*
Acceptance: Chart 1 plots empirical and analytic curves on the same axes and
they agree within 10% at N=120.

**US-4** — *As a reviewer, I want the negative result to be publishable.*
Acceptance: if DSR < 0.95, `outputs/deflation.json` still contains every field
and the README still states the outcome in its first ten lines.

## 7. Success metrics

- Repo runs end to end on a clean clone in one command, in under 30 minutes on
  a laptop CPU (excluding the 90 MB download).
- The bar in `PREREGISTRATION.md` is either met or it is not — and the README
  says which, in one sentence, at the top.
- An interviewer can follow `docs/ARCHITECTURE.md` and re-derive every
  statistic in `src/btrap/` from the docstrings.

## 8. Out of scope

Live execution, brokers, exchanges' private APIs, dashboards, deployment,
multi-asset universes, transaction-cost modelling beyond a fixed bp charge,
and any claim about the marketing article's numbers.
