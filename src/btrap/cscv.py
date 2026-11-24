r"""Probability of Backtest Overfitting by CSCV.

Combinatorially Symmetric Cross-Validation (Bailey, Borwein, Lopez de Prado &
Zhu 2014):

1. Cut the T x N trial-return matrix into S contiguous, equal blocks.
2. For each of the C(S, S/2) ways to choose half the blocks as the in-sample
   set, the complement is out-of-sample.
3. On each split, pick the trial with the best in-sample Sharpe, record its
   out-of-sample rank omega among all trials, and map the rank to a relative
   rank in (0,1). The logit of that relative rank is lambda.
4. PBO = fraction of splits where lambda <= 0, i.e. the in-sample winner lands
   in the bottom half out of sample.

PBO is *not* a corrected Sharpe and it does not detect leakage. It measures
only whether the selection procedure generalises across time halves.
"""

from __future__ import annotations

from itertools import combinations
from math import comb

import numpy as np


def _sharpe_rows(block: np.ndarray) -> np.ndarray:
    mu = block.mean(axis=0)
    sd = block.std(axis=0, ddof=1)
    sd[sd == 0] = np.nan
    return np.nan_to_num(mu / sd, nan=-np.inf)


def pbo(trials: np.ndarray, n_blocks: int = 10) -> dict[str, float]:
    t, n = trials.shape
    if n < 2:
        raise ValueError("need at least two trials")
    if n_blocks % 2:
        n_blocks += 1
    edges = np.linspace(0, t, n_blocks + 1).astype(int)
    blocks = [trials[a:b] for a, b in zip(edges[:-1], edges[1:]) if b > a]
    s = len(blocks)
    lam, omegas = [], []
    for is_idx in combinations(range(s), s // 2):
        is_set = set(is_idx)
        is_block = np.vstack([blocks[i] for i in is_idx])
        oos_block = np.vstack([blocks[i] for i in range(s) if i not in is_set])
        sr_is = _sharpe_rows(is_block)
        sr_oos = _sharpe_rows(oos_block)
        best = int(np.argmax(sr_is))
        # relative rank of the chosen trial's OOS performance, 0 = worst
        rank = (np.argsort(np.argsort(sr_oos))[best] + 0.5) / n
        rank = float(np.clip(rank, 1e-6, 1 - 1e-6))
        omega = np.log(rank / (1 - rank))
        omegas.append(omega)
        lam.append(omega)
    lam = np.asarray(lam)
    return {
        "pbo": float((lam <= 0).mean()),
        "n_splits": int(comb(s, s // 2)),
        "median_logit": float(np.median(lam)),
        "prob_oos_sharpe_positive": float((np.asarray(omegas) > 0).mean()),
    }
