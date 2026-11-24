#!/usr/bin/env python
"""The single sealed read: score the agent's declared winner on the holdout.

Run exactly once. The script refuses a second run unless
``BTRAP_ALLOW_REPEAT=1``, and every run is appended to
``data/holdout/ACCESS_LOG.txt`` by ``btrap.data.load_holdout``.

It reads the winner from ``outputs/deflation.json`` (written by `make dsr`) and
evaluates *that parameter set* on the holdout — not a fresh search. A fresh
search on the holdout would turn the one honest check into another trial.
"""

from __future__ import annotations

import json
import os
import sys

import pandas as pd

from btrap import config, data, engine, ma_rules

RESULT = config.OUT / "holdout_result.json"


def main() -> int:
    if RESULT.exists() and os.environ.get("BTRAP_ALLOW_REPEAT") != "1":
        print(
            f"{RESULT} already exists. The holdout is read once per project.\n"
            "Set BTRAP_ALLOW_REPEAT=1 only if the first read was invalid.",
            file=sys.stderr,
        )
        return 1

    dfile = config.OUT / "deflation.json"
    if not dfile.exists():
        print("run `make dsr` first: no declared winner to test", file=sys.stderr)
        return 1
    winner = json.loads(dfile.read_text(encoding="utf-8"))
    params = winner["best_params"]

    hold = data.load_holdout()
    r = hold["close"].pct_change().dropna().pipe(lambda s: s.apply(lambda x: x))
    r = (hold["close"] / hold["close"].shift(1)).apply(lambda x: x - 1).dropna()

    n_bars = len(r)
    log = engine.TrialLog(config.TRIALS / "holdout.jsonl", "holdout", max_calls=1)
    rec = engine.run(
        lambda ret, short, long: ma_rules.positions(ret, short=short, long=long),
        r,
        log,
        params={"short": int(params["short"]), "long": int(params["long"])},
        tag="holdout_single_read",
    )

    out = {
        "holdout_bars": n_bars,
        "holdout_start": str(hold.index.min()),
        "holdout_end": str(hold.index.max()),
        "params": rec["params"],
        "train_sharpe_annualised": winner["best_sharpe_annualised"],
        "holdout_sharpe_annualised": rec["sharpe_net"],
        "retention_ratio": rec["sharpe_net"] / winner["best_sharpe_annualised"]
        if winner["best_sharpe_annualised"]
        else None,
        "dsr": winner["dsr_neff"],
        "passes_bar": bool(
            winner["dsr_neff"] >= config.DSR_THRESHOLD
            and winner["best_sharpe_annualised"] != 0
            and rec["sharpe_net"] >= 0.5 * winner["best_sharpe_annualised"]
        ),
    }
    RESULT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print("\nNow write the result line at the top of README.md — once, and as-is.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
