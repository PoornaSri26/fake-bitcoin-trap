"""The backtest engine, and the logger that counts trials.

The logger is the whole point of the project. Every call to :func:`run` appends
one JSONL record containing the parameter vector, a hash of the strategy
source, and the net return series. The trial count used in the deflation is
therefore measured, not reported by the agent.

Position convention: ``positions[i]`` is the exposure held from the close of
bar ``i`` to the close of bar ``i+1``. The engine shifts internally, so a
strategy that computes a signal on bar ``i`` is never credited with bar ``i``'s
return. Costs are charged on every change of position, not per round trip.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

BARS_PER_YEAR_HOURLY = 24 * 365


@dataclass(frozen=True)
class CostModel:
    fee_bps: float = 5.0
    slippage_bps: float = 2.0

    @property
    def per_unit_turnover(self) -> float:
        return (self.fee_bps + self.slippage_bps) / 10_000.0


@dataclass
class TrialLog:
    """Append-only trial recorder. One record per backtest call."""

    path: Path
    agent_id: str
    max_calls: int | None = None
    _n: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def n_calls(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open("r", encoding="utf-8") as fh:
            return sum(1 for _ in fh)

    def check_budget(self) -> None:
        if self.max_calls is not None and self.n_calls >= self.max_calls:
            raise RuntimeError(
                f"budget exhausted: {self.n_calls}/{self.max_calls} backtest calls "
                f"for agent {self.agent_id}"
            )

    def write(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        self._n += 1


def code_hash(obj: object) -> str:
    """Stable hash of a strategy's source, so near-duplicate trials are visible."""
    try:
        src = _source_of(obj)
    except OSError:
        src = repr(obj)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]


def _source_of(obj: object) -> str:
    import inspect

    if callable(obj):
        return inspect.getsource(obj)
    return repr(obj)


def net_returns(
    returns: np.ndarray, positions: np.ndarray, cost: CostModel
) -> np.ndarray:
    """Apply positions with one-bar lag and charge turnover costs."""
    r = np.asarray(returns, dtype=float)
    p = np.asarray(positions, dtype=float)
    if r.shape != p.shape:
        raise ValueError(f"shape mismatch: returns {r.shape} vs positions {p.shape}")
    if not np.all(np.isfinite(p)):
        raise ValueError("positions contain NaN/inf — shift(1) and fill before calling")

    gross = np.zeros_like(r)
    gross[1:] = p[:-1] * r[1:]
    turnover = np.zeros_like(r)
    turnover[0] = abs(p[0])
    turnover[1:] = np.abs(np.diff(p))
    return gross - turnover * cost.per_unit_turnover


def sharpe(returns: np.ndarray, periods_per_year: int = BARS_PER_YEAR_HOURLY) -> float:
    """Annualised Sharpe, zero risk-free rate. Non-annualised in DSR maths."""
    r = np.asarray(returns, dtype=float)
    sd = r.std(ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return 0.0
    return float(r.mean() / sd * np.sqrt(periods_per_year))


def run(
    strategy,
    returns: pd.Series,
    log: TrialLog,
    params: dict | None = None,
    cost: CostModel | None = None,
    tag: str = "",
) -> dict:
    """Execute one backtest, log it, and return the summary record.

    ``strategy(returns, **params) -> positions``. The signature is deliberately
    narrow: the agent may not touch prices beyond what it is given.
    """
    log.check_budget()
    cost = cost or CostModel()
    params = dict(params or {})

    r = returns.to_numpy(dtype=float)
    positions = np.asarray(strategy(returns, **params), dtype=float)

    net = net_returns(r, positions, cost)
    trial_id = uuid.uuid4().hex[:12]
    record = {
        "trial_id": trial_id,
        "agent_id": log.agent_id,
        "tag": tag,
        "params": params,
        "code_hash": code_hash(strategy),
        "sharpe_net": sharpe(net),
        "sharpe_gross": sharpe(np.where(np.arange(r.size) > 0, np.r_[0.0, positions[:-1]] * r, 0.0)),
        "mean_net": float(np.nanmean(net)),
        "turnover": float(np.abs(np.diff(positions)).sum()),
        "n_bars": int(r.size),
        "returns": [round(float(x), 10) for x in net],
    }
    log.write(record)
    return {k: v for k, v in record.items() if k != "returns"}


def load_trials(path: Path) -> pd.DataFrame:
    """All logged trials for one agent, with the return series as an array."""
    rows = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    if not rows:
        raise ValueError(f"no trials logged in {path}")
    df = pd.DataFrame(rows)
    df["returns"] = df["returns"].apply(lambda x: np.asarray(x, dtype=float))
    return df


def trial_matrix(df: pd.DataFrame, min_overlap: float = 0.9) -> np.ndarray:
    """T x N matrix of trial returns, trimmed to the length all trials share."""
    lengths = df["returns"].apply(len)
    t = int(lengths.quantile(min_overlap))
    return np.column_stack([r[-t:] for r in df["returns"] if len(r) >= t])
