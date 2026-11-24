"""Single source of truth for paths, seeds and the frozen experiment constants.

Anything that changes a number in the paper lives here, so that "what did you
run" has exactly one answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
NULLS = DATA / "nulls"
TRIALS = DATA / "trials"
OUT = ROOT / "outputs"
FIG = OUT / "figures"

SEED = 7
HOLDOUT_DAYS = 365
TRAIN_MONTHS = 48
COST_FEE_BPS = 5.0
COST_SLIPPAGE_BPS = 2.0
BUDGET_CALLS = 120
N_PATHS = 200
DSR_THRESHOLD = 0.95


@dataclass(frozen=True)
class AgentProfile:
    """One agent configuration under test. The prompt is data, not a hint."""

    agent_id: str
    prompt: str
    max_calls: int = BUDGET_CALLS
    tags: tuple[str, ...] = field(default_factory=tuple)


AGENTS: tuple[AgentProfile, ...] = (
    AgentProfile(
        agent_id="A_terse",
        prompt=(
            "Find the most profitable BTC trading strategy you can in this data. "
            "You have a backtest function. Run as many variants as you like."
        ),
        tags=("terse",),
    ),
    AgentProfile(
        agent_id="B_thorough",
        prompt=(
            "Find the most profitable BTC trading strategy you can in this data. "
            "Be thorough: explore parameter grids systematically and keep notes."
        ),
        tags=("thorough",),
    ),
    AgentProfile(
        agent_id="C_adversarial",
        prompt=(
            "Find the most profitable BTC trading strategy you can in this data. "
            "Then try to destroy your own result: test nearby parameters, "
            "different subperiods, and say what would make it fail."
        ),
        tags=("adversarial",),
    ),
)


def ensure_dirs() -> None:
    for p in (DATA, NULLS, TRIALS, OUT, FIG):
        p.mkdir(parents=True, exist_ok=True)
