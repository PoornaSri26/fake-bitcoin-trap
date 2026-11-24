r"""Deflated Sharpe ratio, probabilistic Sharpe ratio, expected maximum Sharpe.

Every formula is written out above its implementation so it can be re-derived
without the code — which is the point of the exercise.

Notation. ``SR`` is the *non-annualised* per-bar Sharpe of a strategy,
``T`` the number of observations, ``g3`` the skewness of its returns and
``g4`` their (non-excess, normal = 3) kurtosis.

1. Probabilistic Sharpe Ratio (Bailey & Lopez de Prado 2012)
   The Sharpe estimator has standard error ~ sqrt((1 - g3*SR + (g4-1)/4 * SR^2)/(T-1)),
   so

       PSR(SR*) = Phi( (SR - SR*) * sqrt(T-1) / sqrt(1 - g3*SR + (g4-1)/4*SR^2) )

   Deflated Sharpe is PSR evaluated at the threshold SR* that the *best* of N
   tries would reach under the null. It answers: given how hard we searched,
   what is the probability the true Sharpe exceeds zero?

2. Expected maximum of N trial Sharpes (Bailey & Lopez de Prado 2014)
   Under the null the trial Sharpes are approximately iid Normal(0, V) across
   trials with V their cross-trial variance. The maximum of N Gaussians has a
   Gumbel limit, so

       E[max SR] ~ sqrt(V) * ( (1-gamma) * Phi^-1(1 - 1/N)
                                    + gamma   * Phi^-1(1 - 1/(N*e)) )

   with gamma the Euler-Mascheroni constant. This is the analytic curve in
   Chart 1.

3. Deflated Sharpe (the pass/fail quantity)
       DSR = PSR(E[max SR] under N_eff trials).
   Note DSR cannot detect leakage: a strategy that peeks at the future has a
   genuinely high in-sample Sharpe and a legitimately small N.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

EULER_GAMMA = 0.5772156649015329


def sharpe_per_bar(returns: np.ndarray) -> float:
    r = np.asarray(returns, dtype=float)
    sd = r.std(ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return 0.0
    return float(r.mean() / sd)


def moments(returns: np.ndarray) -> tuple[float, float]:
    """(skewness, kurtosis) with kurtosis in the non-excess convention."""
    r = np.asarray(returns, dtype=float)
    g3 = float(stats.skew(r, bias=False))
    g4 = float(stats.kurtosis(r, fisher=False, bias=False))
    return g3, g4


def psr(returns: np.ndarray, sr_star: float = 0.0) -> float:
    """P(true per-bar Sharpe > sr_star), with skew/kurtosis adjustment."""
    r = np.asarray(returns, dtype=float)
    t = r.size
    if t < 3:
        return float("nan")
    sr = sharpe_per_bar(r)
    g3, g4 = moments(r)
    denom = 1.0 - g3 * sr + 0.25 * (g4 - 1.0) * sr**2
    if denom <= 0:
        return float("nan")
    z = (sr - sr_star) * np.sqrt(t - 1) / np.sqrt(denom)
    return float(stats.norm.cdf(z))


def expected_max_sharpe(n_trials: float, sr_variance: float) -> float:
    """Analytic E[max] of n_trials iid Gaussian trial Sharpes, via Gumbel."""
    n = max(float(n_trials), 1.0)
    if sr_variance <= 0 or not np.isfinite(sr_variance):
        return 0.0
    a = stats.norm.ppf(1.0 - 1.0 / n)
    b = stats.norm.ppf(1.0 - 1.0 / (n * np.e))
    return float(np.sqrt(sr_variance) * ((1.0 - EULER_GAMMA) * a + EULER_GAMMA * b))


@dataclass(frozen=True)
class Deflation:
    n_trials_raw: int
    n_eff: float
    trial_sr_variance: float
    sr_threshold: float
    best_sr_per_bar: float
    best_sr_annualised: float
    threshold_annualised: float
    dsr: float

    @property
    def passes(self) -> bool:
        return self.dsr >= 0.95


def deflate(
    best_returns: np.ndarray,
    trial_sr_variance: float,
    n_trials_raw: int,
    n_eff: float | None = None,
    periods_per_year: int = 24 * 365,
    threshold: float = 0.95,
) -> Deflation:
    """The project's headline number.

    ``n_eff`` defaults to ``n_trials_raw`` (the conservative, un-clustered
    choice). Passing the participation-ratio estimate shrinks the threshold and
    makes the test *easier* to pass, so both are reported.
    """
    n_eff = float(n_trials_raw if n_eff is None else n_eff)
    thr = expected_max_sharpe(n_eff, trial_sr_variance)
    r = np.asarray(best_returns, dtype=float)
    sr = sharpe_per_bar(r)
    return Deflation(
        n_trials_raw=int(n_trials_raw),
        n_eff=n_eff,
        trial_sr_variance=float(trial_sr_variance),
        sr_threshold=thr,
        best_sr_per_bar=sr,
        best_sr_annualised=sr * np.sqrt(periods_per_year),
        threshold_annualised=thr * np.sqrt(periods_per_year),
        dsr=psr(r, sr_star=thr),
    )
