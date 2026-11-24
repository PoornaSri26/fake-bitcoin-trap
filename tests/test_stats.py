"""Checks the statistics modules against their closed-form limits.

These are the tests a interviewer would ask for: does the estimator do what the
formula says in a case where the answer is known.
"""

from __future__ import annotations

import numpy as np
import pytest

from btrap import dsr, neff
from btrap.engine import CostModel, net_returns, sharpe


def test_psr_of_exactly_zero_sharpe_is_half():
    # PSR(SR*=0) tests whether the true per-bar Sharpe exceeds zero. With
    # T = 20,000 even a 0.003 sample Sharpe is "significant", so the series must
    # be mean-centred to have a *known* zero Sharpe; that is the case with a
    # closed-form answer.
    rng = np.random.default_rng(0)
    r = rng.normal(0.0, 1.0, 5_000)
    r = r - r.mean()
    assert abs(dsr.psr(r) - 0.5) < 1e-9


def test_psr_is_uniformish_under_the_null():
    # Small T so sampling noise dominates the drift: PSR should hover near 0.5
    # and never be extreme.
    rng = np.random.default_rng(11)
    vals = [dsr.psr(rng.normal(0.0, 1.0, 300)) for _ in range(200)]
    assert 0.35 < np.mean(vals) < 0.65
    assert max(vals) < 0.999


def test_psr_monotone_in_drift():
    rng = np.random.default_rng(1)
    base = rng.normal(0.0, 1.0, 5_000)
    lo = dsr.psr(base)
    hi = dsr.psr(base + 0.05)
    assert hi > lo


def test_expected_max_grows_with_trials_and_is_positive():
    a = dsr.expected_max_sharpe(10, 1e-4)
    b = dsr.expected_max_sharpe(1_000, 1e-4)
    assert 0 < a < b


def test_expected_max_matches_monte_carlo():
    rng = np.random.default_rng(2)
    n, k = 120, 400_000
    v = 1e-4
    draws = rng.normal(0.0, np.sqrt(v), size=(k // n, n)).max(axis=1)
    analytic = dsr.expected_max_sharpe(n, v)
    assert abs(draws.mean() - analytic) / analytic < 0.05


def test_deflate_penalises_higher_trial_counts():
    rng = np.random.default_rng(3)
    best = rng.normal(8e-4, 1e-2, 5_000)
    d_few = dsr.deflate(best, trial_sr_variance=1e-4, n_trials_raw=10)
    d_many = dsr.deflate(best, trial_sr_variance=1e-4, n_trials_raw=5_000)
    assert d_many.dsr < d_few.dsr
    assert d_many.threshold_annualised > d_few.threshold_annualised


def test_participation_ratio_of_independent_series_is_n():
    rng = np.random.default_rng(4)
    x = rng.normal(size=(4_000, 20))
    assert abs(neff.participation_ratio(x) - 20) < 3


def test_participation_ratio_of_duplicated_series_is_one():
    rng = np.random.default_rng(5)
    x = rng.normal(size=(4_000, 1))
    assert neff.participation_ratio(np.hstack([x] * 10)) < 1.2


def test_cost_model_charges_turnover_not_round_trips():
    r = np.zeros(4)
    pos = np.array([1.0, 1.0, -1.0, -1.0])
    net = net_returns(r, pos, CostModel(fee_bps=5.0, slippage_bps=2.0))
    # entry at t0 (1 unit) plus reversal at t2 (2 units) = 3 units of turnover
    assert net.sum() == pytest.approx(-3 * 7e-4)


def test_sharpe_of_constant_series_is_zero():
    assert sharpe(np.ones(100)) == 0.0
