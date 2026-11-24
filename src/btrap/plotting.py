"""Figure design tokens. The single source of truth for chart appearance.

See docs/DESIGN_SYSTEM.md. Never hard-code a hex value or a font size in a
plotting function; add a token here instead.
"""

from __future__ import annotations

TOKENS = {
    "ink": "#111318",
    "grid": "#D6DAE1",
    "empirical": "#3B6EA5",
    "analytic": "#1B1F26",
    "pass": "#2E7D32",
    "fail": "#B3261E",
    "muted": "#6B7280",
}

FIGSIZE_SINGLE = (7.0, 4.5)
FIGSIZE_BAR = (6.0, 4.0)
DPI = 160


def apply_style() -> None:
    """Apply the project's matplotlib defaults. Call once per process."""
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": TOKENS["ink"],
            "axes.labelcolor": TOKENS["ink"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": TOKENS["grid"],
            "grid.linewidth": 0.6,
            "grid.alpha": 0.7,
            "text.color": TOKENS["ink"],
            "xtick.color": TOKENS["ink"],
            "ytick.color": TOKENS["ink"],
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "legend.frameon": False,
            "lines.linewidth": 1.4,
            "savefig.dpi": DPI,
        }
    )


def threshold_line(ax, value: float, label: str) -> None:
    """Dashed bar with its value at the right end. No legend entry."""
    ax.axhline(value, ls="--", lw=1.0, color=TOKENS["fail"])
    ax.annotate(
        label,
        xy=(1.0, value),
        xycoords=("axes fraction", "data"),
        xytext=(-4, 4),
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=8,
        color=TOKENS["muted"],
    )
