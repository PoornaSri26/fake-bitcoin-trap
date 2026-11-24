# SECURITY — The Fake Bitcoin Trap

This project handles no user data and needs no API keys. The security concerns
are therefore about **integrity of the experiment** and **respect for the data
provider's terms**, not about accounts.

## 1. Secrets

| Secret | Needed? | Where |
|---|---|---|
| exchange API keys | **no** | never requested, never accepted |
| OpenAI/Anthropic keys (agent runs) | yes, if you run a real agent | `.env`, gitignored |
| anything else | no | — |

Rules:
- `.env` is gitignored; `.env.example` lists names only, with no values.
- Never paste a key into a prompt, an issue, or a commit message.
- The trial log must not contain keys. `engine.run` records params, not
  environment variables; keep it that way.

`.gitignore` includes `.env*` with `!.env.example`.

## 2. Integrity controls (the real subject here)

| Control | What it prevents | Where |
|---|---|---|
| Pre-registration + sha256 | moving the bar after seeing results | `PREREGISTRATION.md`, `make stamp` |
| Holdout outside the working tree | accidental look-ahead | `seal_holdout.py`, `load_holdout` env gate |
| Append-only trial log with code hash | under-reported trials, silent re-runs | `engine.TrialLog` |
| One-shot holdout with an access log | p-hacking on the test set | `run_holdout.py` |
| Budget cap per agent | unbounded search reported as "one strategy" | `TrialLog.max_calls` |

If the holdout is ever visible to the agent sandbox, the experiment is **void**.
That is stated in the pre-registration and must be stated in the README.

## 3. Authorisation of network access

| Host | Why | Constraint |
|---|---|---|
| `data.binance.vision` | klines | public, no auth, checksums verified |

- Rate: one request per month file, sequentially. No parallelism needed; do not
  add it.
- Re-downloading is idempotent and checksum-verified.
- The project never calls a trading endpoint and never sends an order.

## 4. Data handling

- No personal data is collected. Klines are public market data.
- No redistribution of bulk data in the repo: `data/` is gitignored and the
  README links to the source and the download script instead.
- Cite the source and note the 2025-01-01 timestamp change when reporting.

## 5. Dependency hygiene

- Five direct dependencies plus `arch`. Pin lower bounds in `requirements.txt`.
- Before adding a dependency, ask: does numpy or scipy already do this?
- `pip install` in a virtualenv, never system-wide.
- No dependency is allowed to make network calls at import time.

## 6. Slips that would be serious

| Slip | Why it is serious | Detection |
|---|---|---|
| Committing `data/holdout/*.parquet` | destroys the one honest check | `.gitignore` + a pre-commit grep for `holdout` |
| Editing a JSONL line | falsifies the trial count | files are append-only; `git diff` on `data/` is impossible because it is ignored — so hash the log in the run report |
| Quoting a trial the harness did not log | overclaiming | `deflation.json` names a `trial_id` that must exist in the log; add that check |
| Publishing a Sharpe without its N | misleading by omission | the report template has an `N=` field that cannot be blank |

## 7. Pre-publication checklist

- [ ] `PREREGISTRATION.sha256` matches the committed file.
- [ ] `data/` and `outputs/` are not in git.
- [ ] No key appears in `git log -p` (`git grep -i -E "sk-|api[_-]?key"`).
- [ ] The README states the result, the bar and the trial count.
- [ ] The holdout result is present exactly once, or explicitly absent with a
      reason.
