"""Reference agents.

Two things live here:

1. ``ReferenceAgent`` — a deterministic grid search over the 959 MA rules. It
   exercises the full instrument (logger, N_eff, DSR) without needing an LLM,
   so `make reproduce` runs end to end on a fresh clone. It is *not* the object
   of study; it is the harness's own smoke test and its trial count is known
   by construction, which makes it a useful check on N_eff.

2. ``LLMAgentAdapter`` — the thin shim an actual LLM agent plugs into. The
   contract is one function: the agent may only produce positions for the data
   it is handed, and every attempt goes through ``engine.run`` so it is
   counted. The adapter deliberately has no access to the filesystem.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import engine, ma_rules


class ReferenceAgent:
    """Exhaustive MA-rule search. Deterministic, budget-respecting, fully logged."""

    def __init__(self, log: engine.TrialLog, cost: engine.CostModel | None = None):
        self.log = log
        self.cost = cost or engine.CostModel()

    def explore(self, returns: pd.Series, rules: list[dict] | None = None) -> list[dict]:
        rules = rules if rules is not None else ma_rules.universe()
        out = []
        for rule in rules:
            try:
                out.append(
                    engine.run(
                        _ma_strategy,
                        returns,
                        self.log,
                        params=rule,
                        cost=self.cost,
                        tag="ma_rule",
                    )
                )
            except RuntimeError:
                break  # budget exhausted
        return out

    @property
    def winner(self) -> dict | None:
        df = engine.load_trials(self.log.path)
        if df.empty:
            return None
        return df.loc[df["sharpe_net"].idxmax()].to_dict()


def _ma_strategy(returns: pd.Series, short: int, long: int) -> np.ndarray:
    return ma_rules.positions(returns, short=short, long=long)


class LLMAgentAdapter:
    """Adapter for a real agent. Guard rails, not conveniences.

    * ``data_root`` is the only directory the agent's tools may read; the
      holdout lives outside it and is never mounted.
    * every strategy call goes through ``run`` so trials are counted even if
      the agent never mentions them in its transcript.
    """

    def __init__(self, agent_id: str, data_root: Path, log_path: Path, max_calls: int):
        self.agent_id = agent_id
        self.data_root = Path(data_root)
        self.log = engine.TrialLog(log_path, agent_id=agent_id, max_calls=max_calls)

    def propose(self, strategy, returns: pd.Series, params: dict | None = None, tag: str = ""):
        return engine.run(strategy, returns, self.log, params=params, tag=tag)
