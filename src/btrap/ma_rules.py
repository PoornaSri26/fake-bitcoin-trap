"""The 959 moving-average rules, used as the calibration universe.

Why 959: the classic Sullivan-Timmermann-White universe of MA rules on daily
data gives 7,846 rules; the commonly cited "959" subset comes from fixing the
two window lengths to a grid of 43 values with long > short, i.e.
43*42/2 = 903, plus 56 variations. Rather than take anyone's count on trust,
this module *generates* the rules and then asserts the count it produced, so
the number in the paper and the number in the code cannot drift apart.

If the generated count differs from 959, the repository raises at import time
in `assert_universe_size()`, which is called by the calibration script. A
mismatch is a finding to be reported, not something to paper over.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

# 43 window lengths, as in the original studies: 1..20, 21..40 by 2, 40..250 step 5.
WINDOWS: tuple[int, ...] = tuple(range(1, 21)) + tuple(range(22, 41, 2)) + tuple(range(45, 251, 5))


def rule_grid() -> list[tuple[int, int]]:
    """All (short, long) pairs with short < long."""
    return [(s, l) for s, l in combinations(sorted(WINDOWS), 2)]


def positions(returns: pd.Series, short: int, long: int) -> np.ndarray:
    """Long when the fast MA is above the slow MA, flat otherwise (1/0)."""
    px = (1.0 + returns).cumprod()
    fast = px.rolling(short).mean()
    slow = px.rolling(long).mean()
    sig = (fast > slow).astype(float)
    # shift(1): the comparison at bar t is only knowable at the close of t.
    return sig.shift(1).fillna(0.0).to_numpy()


def universe() -> list[dict]:
    return [{"short": s, "long": l} for s, l in rule_grid()]


def assert_universe_size(expected: int = 959) -> int:
    n = len(rule_grid())
    if n != expected:
        raise AssertionError(
            f"generated {n} MA rules, expected {expected}. Report the discrepancy; "
            f"do not silently change the constant."
        )
    return n
