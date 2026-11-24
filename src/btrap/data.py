"""Kline loading, truncation, and holdout sealing.

Design rule: the holdout is not reachable by accident. Everything that trains
or backtests calls ``load_train()``, which truncates at the boundary. Only
``load_holdout()`` reads the sealed file, and it refuses unless the env var
``BTRAP_RELEASE_HOLDOUT`` is set to ``1``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
HOLDOUT_DIR = DATA / "holdout"

HOLDOUT_DAYS = 365
_BAR = pd.Timedelta(hours=1)

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
    "ignore",
]


class HoldoutAccessError(RuntimeError):
    pass


@dataclass(frozen=True)
class Split:
    train: pd.DataFrame
    holdout_start: pd.Timestamp

    @property
    def boundary(self) -> pd.Timestamp:
        return self.holdout_start


def _read_klines(path: Path) -> pd.DataFrame:
    """Read a CSV or Parquet kline dump into a UTC-indexed frame."""
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, header=None, names=KLINE_COLUMNS)
        # data.binance.vision spot files carry a header row in some months and
        # not in others: drop it if the first row is the literal column names.
        if str(df["open_time"].iloc[0]).lower().startswith("open"):
            df = df.iloc[1:].reset_index(drop=True)
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in ("open_time", "close_time"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("int64")

    # Binance switched SPOT timestamps to microseconds on 2025-01-01. A file can
    # therefore straddle nothing, but a merged frame can mix units: normalise.
    t = df["open_time"].to_numpy(dtype="int64")
    unit = np.where(t > 10**14, 1e6, 1e3)
    ts = pd.to_datetime(t / unit, unit="s", utc=True)
    out = df.assign(open_time=ts).set_index("open_time").sort_index()
    return out[["open", "high", "low", "close", "volume"]].astype("float64")


def load_all() -> pd.DataFrame:
    """All klines found under ``data/raw``, de-duplicated and sorted."""
    files = sorted(list(RAW.glob("BTCUSDT-1h-*.csv")) + list(RAW.glob("BTCUSDT-1h-*.parquet")))
    if not files:
        raise FileNotFoundError(
            f"no klines in {RAW}. Run: python scripts/download_data.py --months 60"
        )
    frames = [_read_klines(f) for f in files]
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df


def holdout_boundary(df: pd.DataFrame) -> pd.Timestamp:
    return df.index.max() - pd.Timedelta(days=HOLDOUT_DAYS) - _BAR


def split(df: pd.DataFrame) -> Split:
    b = holdout_boundary(df)
    return Split(train=df.loc[df.index <= b].copy(), holdout_start=b + _BAR)


def load_train() -> tuple[pd.DataFrame, pd.Timestamp]:
    """Training data plus the timestamp at which the holdout begins."""
    s = split(load_all())
    return s.train, s.holdout_start


def log_returns(df: pd.DataFrame) -> pd.Series:
    return np.log(df["close"]).diff().dropna()


def load_holdout() -> pd.DataFrame:
    """The single, deliberate, once-per-project read of the sealed months."""
    if os.environ.get("BTRAP_RELEASE_HOLDOUT") != "1":
        raise HoldoutAccessError(
            "Holdout is sealed. Set BTRAP_RELEASE_HOLDOUT=1 and use "
            "scripts/run_holdout.py — one read per project, recorded in "
            "data/holdout/ACCESS_LOG.txt."
        )
    path = HOLDOUT_DIR / "btcusdt_1h_holdout.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing. Run scripts/seal_holdout.py first.")
    log = HOLDOUT_DIR / "ACCESS_LOG.txt"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"{pd.Timestamp.utcnow().isoformat()}\t{os.environ.get('USER', '?')}\n")
    return pd.read_parquet(path)
