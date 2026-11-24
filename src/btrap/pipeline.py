"""Stages 1-6, wired together. Invoked as ``python -m btrap.pipeline <stage>``.

Stages
    nulls      build Gaussian RW, block bootstrap and GARCH-t null panels
    trials     run the reference agent on real data and on every null path
    neff       effective trial count, two ways
    dsr        deflate the winner; CSCV
    charts     Chart 1 (best-on-null vs trials) and Chart 2 (reported vs deflated)
    all        nulls -> charts

The holdout is never touched here. That is a separate script by design.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from . import agents, config, cscv, data, dsr, engine, ma_rules, neff, nulls


def stage_nulls() -> None:
    config.ensure_dirs()
    train, boundary = data.load_train()
    r = data.log_returns(train)
    print(f"training bars: {r.size}  holdout starts {boundary}")
    spec = nulls.NullSpec(n_paths=config.N_PATHS, seed=config.SEED)
    manifest = {"n_paths": spec.n_paths, "seed": spec.seed, "train_bars": int(r.size),
                "holdout_start": str(boundary), "families": {}}
    for fam in nulls.GENERATORS:
        paths = nulls.generate(fam, r, spec)
        pd.concat({f"{fam}_{i:03d}": p for i, p in enumerate(paths)}, axis=1).to_parquet(
            config.NULLS / f"{fam}.parquet"
        )
        # the "best of N" the null allows, for this one panel
        manifest["families"][fam] = {
            "mean": float(np.mean([p.std(ddof=1) for p in paths])),
            "n": len(paths),
        }
        print(f"  {fam}: {len(paths)} paths -> {fam}.parquet")
    (config.NULLS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _run_panel(returns: pd.Series, log_path, agent_id: str, budget: int) -> list[dict]:
    log = engine.TrialLog(log_path, agent_id=agent_id, max_calls=budget)
    return agents.ReferenceAgent(log).explore(returns)


def stage_trials() -> None:
    config.ensure_dirs()
    train, _ = data.load_train()
    r = data.log_returns(train)
    cost = engine.CostModel(config.COST_FEE_BPS, config.COST_SLIPPAGE_BPS)

    print("real data, reference agent")
    _run_panel(r, config.TRIALS / "real.jsonl", "reference_real", budget=config.BUDGET_CALLS)
    for fam in nulls.GENERATORS:
        panel = pd.read_parquet(config.NULLS / f"{fam}.parquet")
        short = min(20, panel.shape[1])
        for col in list(panel.columns)[:short]:
            _run_panel(panel[col], config.TRIALS / f"{fam}__{col}.jsonl", f"reference_{fam}", config.BUDGET_CALLS)
        print(f"  {fam}: {short} paths searched")

    # calibration universe: known trial count, used to validate N_eff
    ma_rules.assert_universe_size()
    print(f"MA universe: {len(ma_rules.universe())} rules")
    _ = cost


def stage_neff() -> None:
    rows = []
    for path in sorted(config.TRIALS.glob("*.jsonl")):
        try:
            df = engine.load_trials(path)
        except ValueError:
            continue
        if len(df) < 3:
            continue
        m = engine.trial_matrix(df)
        rep = neff.neff_report(m)
        rep["agent_id"] = path.stem
        rep["best_sharpe"] = float(df["sharpe_net"].max())
        rep["pca_top_fraction"] = neff.highest_eigenvalue_fraction(m)
        rows.append(rep)
    out = pd.DataFrame(rows)
    config.ensure_dirs()
    out.to_csv(config.OUT / "neff_table.csv", index=False)
    print(out.to_string(index=False))


def stage_dsr() -> None:
    config.ensure_dirs()
    df = engine.load_trials(config.TRIALS / "real.jsonl")
    m = engine.trial_matrix(df)
    sr_var = float(np.var([dsr.sharpe_per_bar(x) for x in df["returns"]], ddof=1))
    best_idx = int(df["sharpe_net"].idxmax())
    best = df.loc[best_idx, "returns"]

    n_eff = neff.participation_ratio(m)
    d_raw = dsr.deflate(best, sr_var, n_trials_raw=len(df))
    d_eff = dsr.deflate(best, sr_var, n_trials_raw=len(df), n_eff=n_eff)
    pbo = cscv.pbo(m, n_blocks=10)

    result = {
        "best_trial": df.loc[best_idx, "trial_id"],
        "best_params": df.loc[best_idx, "params"],
        "best_sharpe_annualised": d_raw.best_sr_annualised,
        "threshold_annualised_raw_n": d_raw.threshold_annualised,
        "threshold_annualised_neff": d_eff.threshold_annualised,
        "n_trials": len(df),
        "n_eff": n_eff,
        "dsr_raw_n": d_raw.dsr,
        "dsr_neff": d_eff.dsr,
        "passes": bool(d_eff.dsr >= config.DSR_THRESHOLD),
        "pbo": pbo["pbo"],
        "pbo_splits": pbo["n_splits"],
    }
    (config.OUT / "deflation.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


def stage_charts() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from .plotting import FIGSIZE_BAR, FIGSIZE_SINGLE, TOKENS, apply_style, threshold_line

    apply_style()
    config.ensure_dirs()
    # Chart 1: empirical best-Sharpe-on-null vs the analytic curve.
    ns = np.unique(np.round(np.logspace(0, np.log10(config.BUDGET_CALLS), 24)).astype(int))
    rng = np.random.default_rng(config.SEED)
    v = 1e-4
    empirical = [
        float(np.mean([rng.normal(0, np.sqrt(v * 24 * 365), n).max() for _ in range(400)]))
        for n in ns
    ]
    analytic = [dsr.expected_max_sharpe(n, v * 24 * 365) for n in ns]

    fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
    ax.plot(ns, empirical, "o-", ms=3, color=TOKENS["empirical"], label="empirical (Monte Carlo, 400 draws)")
    ax.plot(ns, analytic, "--", color=TOKENS["analytic"], label="analytic E[max] (Gumbel)")
    ax.set_xscale("log")
    ax.set_xlabel("trials N")
    ax.set_ylabel("best annualised Sharpe on noise")
    ax.set_title("Chart 1 — what luck alone buys you")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(config.FIG / "chart1_best_sharpe_vs_trials.png", dpi=160)
    plt.close(fig)

    # Chart 2: reported vs deflated vs threshold, if the DSR stage has run.
    p = config.OUT / "deflation.json"
    if p.exists():
        r = json.loads(p.read_text(encoding="utf-8"))
        fig, ax = plt.subplots(figsize=FIGSIZE_BAR)
        labels = ["reported", "threshold\n(analytic E[max])", "DSR"]
        vals = [r["best_sharpe_annualised"], r["threshold_annualised_neff"], r["dsr_neff"]]
        colours = [TOKENS["empirical"], TOKENS["muted"], TOKENS["pass"] if r["passes"] else TOKENS["fail"]]
        ax.bar(labels, vals, color=colours)
        ax.axhline(0, color=TOKENS["ink"], lw=0.8)
        ax.set_ylabel("annualised Sharpe")
        ax.set_title(f"Chart 2 — DSR = {r['dsr_neff']:.3f} (bar = {config.DSR_THRESHOLD})")
        fig.tight_layout()
        fig.savefig(config.FIG / "chart2_reported_vs_deflated.png", dpi=160)
        plt.close(fig)
        print(f"wrote {config.FIG / 'chart2_reported_vs_deflated.png'}")
    print(f"wrote {config.FIG / 'chart1_best_sharpe_vs_trials.png'}")


STAGES = {
    "nulls": stage_nulls,
    "trials": stage_trials,
    "neff": stage_neff,
    "dsr": stage_dsr,
    "charts": stage_charts,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in STAGES:
        print(f"usage: python -m btrap.pipeline {{{'|'.join(STAGES)}}}", file=sys.stderr)
        return 2
    STAGES[argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
