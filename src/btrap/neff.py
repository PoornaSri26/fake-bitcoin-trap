r"""Effective number of independent trials, two independent ways.

Why correlation shrinks N: if two strategies are 95% correlated their Sharpes
are near-identical, so the second one adds almost no new chance of a lucky
maximum. Deflating as if you had N independent tries over-penalises; deflating
as if you had 1 under-penalises. N_eff sits between.

Estimator (a) — participation ratio of the trial covariance spectrum:

    N_eff = (sum_i lambda_i)^2 / sum_i lambda_i^2

This is a spectral "how many directions is this cloud actually spread over".
It is cheap, parameter-free, and needs no clustering. It over-counts when a
few huge factors dominate the spectrum.

Estimator (b) — ONC-style clustering (Lopez de Prado & Lewis 2019, "Detection
of false investment strategies"). Cluster the trial return series by
correlation distance, then count clusters. The published ONC uses a
Kolmogorov-Smirnov quality test per split; this implementation approximates
that with a silhouette-optimal cut of an average-linkage dendrogram and is
labelled as an approximation wherever the number is reported.

Report both. Where they disagree by more than 2x, say so — that disagreement is
itself a result about how the agent searched.
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform


def corr_matrix(trials: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Correlation of columns of a T x N matrix, nan-safe."""
    x = np.asarray(trials, dtype=float)
    x = x - x.mean(axis=0, keepdims=True)
    sd = x.std(axis=0, ddof=1, keepdims=True)
    sd[sd < eps] = np.nan
    c = (x / sd).T @ (x / sd) / (x.shape[0] - 1)
    c = np.nan_to_num(c, nan=0.0)
    np.fill_diagonal(c, 1.0)
    return np.clip(c, -1.0, 1.0)


def participation_ratio(trials: np.ndarray) -> float:
    """(sum lambda)^2 / sum lambda^2 over the eigenvalues of the trial covariance."""
    c = corr_matrix(trials)
    lam = np.linalg.eigvalsh(c)
    lam = np.clip(lam, 0.0, None)
    denom = float(np.sum(lam**2))
    if denom <= 0:
        return float("nan")
    return float(np.sum(lam) ** 2 / denom)


def _corr_distance(c: np.ndarray) -> np.ndarray:
    # d = sqrt(0.5 * (1 - rho)) is a proper metric on correlation.
    d = np.sqrt(np.clip(0.5 * (1.0 - c), 0.0, None))
    np.fill_diagonal(d, 0.0)
    return d


def onc_clusters(trials: np.ndarray, max_clusters: int = 50) -> int:
    """Approximate ONC: average-linkage on correlation distance, silhouette cut.

    Approximation note: the published algorithm tests each candidate split with
    a KS statistic against a null of no cluster structure. Silhouette is used
    here because it is stable and needs no distributional assumption; the number
    it returns is reported as "ONC (approx)".
    """
    c = corr_matrix(trials)
    n = c.shape[0]
    if n < 3:
        return max(n, 1)
    d = _corr_distance(c)
    z = linkage(squareform(d, checks=False), method="average")

    best_k, best_score = 1, -np.inf
    for k in range(2, min(max_clusters, n - 1) + 1):
        labels = fcluster(z, k, criterion="maxclust")
        score = _silhouette(d, labels)
        if score > best_score:
            best_k, best_score = k, score
    return int(best_k)


def _silhouette(d: np.ndarray, labels: np.ndarray) -> float:
    uniq = np.unique(labels)
    if uniq.size < 2:
        return -np.inf
    s = []
    for i in range(d.shape[0]):
        same = (labels == labels[i])
        same[i] = False
        if same.sum() == 0:
            s.append(0.0)
            continue
        a = d[i, same].mean()
        b = min(d[i, labels == u].mean() for u in uniq if u != labels[i])
        m = max(a, b)
        s.append(0.0 if m == 0 else (b - a) / m)
    return float(np.mean(s))


def neff_report(trials: np.ndarray) -> dict[str, float]:
    return {
        "n_trials": int(trials.shape[1]),
        "n_eff_participation_ratio": participation_ratio(trials),
        "n_eff_onc_approx": onc_clusters(trials),
        "mean_pairwise_corr": float(
            corr_matrix(trials)[np.triu_indices(trials.shape[1], k=1)].mean()
        ),
    }


def highest_eigenvalue_fraction(trials: np.ndarray) -> float:
    """Share of total trial variance in the first PC. Large => the agent was
    effectively re-running one idea, and N_eff is far below N."""
    lam = np.clip(np.linalg.eigvalsh(corr_matrix(trials)), 0.0, None)
    return float(lam[-1] / lam.sum())
