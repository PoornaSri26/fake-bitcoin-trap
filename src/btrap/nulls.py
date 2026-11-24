"""Null worlds that keep the awkward parts of the data.

Three families, in increasing order of how well they imitate BTC:

A. Gaussian random walk matched to BTC's mean and per-bar volatility.
   Destroys volatility clustering, fat tails, and any autocorrelation. This is
   the *easy* null; anything surviving A is not obviously noise.

B. Stationary block bootstrap of real returns (block length 24 bars = 1 day).
   Keeps fat tails, keeps volatility clustering inside a block, destroys the
   cross-block structure that a real trend would live in.

C. GARCH(1,1) with Student-t innovations, refitted to the training returns.
   Keeps clustering and tails *and* generates them from a parametric law, so
   the series is not made of recycled real blocks. This is "the trap inside the
   trap": under C, volatility-timing strategies look genuinely skilled.

Every generator returns a Series indexed like the training data so that the
agent's strategies see the same clock.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NullSpec:
    n_paths: int = 200
    seed: int = 7
    block: int = 24


def gaussian_rw(returns: pd.Series, rng: np.random.Generator) -> pd.Series:
    mu = float(returns.mean())
    sd = float(returns.std(ddof=1))
    draws = rng.normal(mu, sd, size=returns.size)
    return pd.Series(draws, index=returns.index, name="null_A")


def block_bootstrap(returns: pd.Series, rng: np.random.Generator, block: int = 24) -> pd.Series:
    """Stationary bootstrap: geometric block lengths with mean ``block``."""
    r = returns.to_numpy(dtype=float)
    n = r.size
    p = 1.0 / max(block, 1)
    out = np.empty(n)
    i = rng.integers(0, n)
    for t in range(n):
        out[t] = r[i % n]
        if rng.random() < p:
            i = rng.integers(0, n)
        else:
            i += 1
    return pd.Series(out, index=returns.index, name="null_B")


def garch_t(returns: pd.Series, rng: np.random.Generator) -> pd.Series:
    """Simulate GARCH(1,1) with Student-t innovations fitted to ``returns``.

    Falls back to a moment-matched t-GARCH if ``arch`` is not installed, which
    keeps `make reproduce` runnable without the optional dependency.
    """
    try:
        from arch import arch_model
    except ImportError:
        return _fallback_garch_t(returns, rng)

    scaled = returns.to_numpy(dtype=float) * 100.0  # arch prefers percent scale
    am = arch_model(scaled, mean="Constant", vol="GARCH", p=1, q=1, dist="t", rescale=False)
    res = am.fit(disp="off", show_warning=False)
    sim = res.model.simulate(res.params, nobs=returns.size, burn=200, seed=int(rng.integers(1 << 31)))
    sim = np.asarray(sim["data"]).ravel()[-returns.size :] / 100.0
    return pd.Series(sim, index=returns.index, name="null_C")


def _fallback_garch_t(returns: pd.Series, rng: np.random.Generator) -> pd.Series:
    r = returns.to_numpy(dtype=float)
    var = float(np.var(r))
    omega = 0.05 * var
    alpha, beta = 0.10, 0.85
    # t innovations rescaled to unit variance, nu matched loosely to excess kurtosis
    excess = float(pd.Series(r).kurt())
    nu = max(4.0, 6.0 / max(excess, 1e-3) + 4.0)
    z = rng.standard_t(nu, size=r.size) * np.sqrt((nu - 2) / nu)
    out = np.empty(r.size)
    s2 = var
    for t in range(r.size):
        out[t] = np.sqrt(s2) * z[t]
        s2 = omega + alpha * out[t] ** 2 + beta * s2
    return pd.Series(out, index=returns.index, name="null_C")


GENERATORS = {
    "A_gaussian_rw": gaussian_rw,
    "B_block_bootstrap": block_bootstrap,
    "C_garch_t": garch_t,
}


def generate(family: str, returns: pd.Series, spec: NullSpec) -> list[pd.Series]:
    """All paths for one null family, seeded deterministically."""
    fn = GENERATORS[family]
    out = []
    for i in range(spec.n_paths):
        rng = np.random.default_rng((spec.seed, i, hash(family) % 10_000))
        if family == "B_block_bootstrap":
            out.append(fn(returns, rng, block=spec.block))
        else:
            out.append(fn(returns, rng))
    return out


def best_sharpe_on_null(sharpes: np.ndarray) -> dict[str, float]:
    """Summary of the 'best of N tries' distribution across null paths."""
    s = np.asarray(sharpes, dtype=float)
    return {
        "mean": float(s.mean()),
        "sd": float(s.std(ddof=1)),
        "p50": float(np.quantile(s, 0.50)),
        "p90": float(np.quantile(s, 0.90)),
        "p95": float(np.quantile(s, 0.95)),
        "p99": float(np.quantile(s, 0.99)),
        "max": float(s.max()),
    }
