"""btrap — the Fake Bitcoin Trap harness.

Submodules:
    data       klines, train/holdout split, holdout sealing
    engine     backtest + the trial logger that counts tries
    ma_rules   the 959-rule calibration universe
    nulls      Gaussian RW / block bootstrap / GARCH-t null worlds
    neff       participation ratio and ONC-style cluster count
    dsr        PSR, expected max Sharpe, deflated Sharpe
    cscv       probability of backtest overfitting
"""

__version__ = "0.1.0"
