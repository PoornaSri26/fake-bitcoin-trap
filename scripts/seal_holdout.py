#!/usr/bin/env python
"""Seal the final 12 months into a directory the agent sandbox never mounts.

Run after `download_data.py`. Idempotent: if the holdout file already exists it
is left untouched (re-sealing a different window would be a silent redefinition
of the experiment).
"""

from __future__ import annotations

import pandas as pd

from btrap import config, data

HOLDOUT_DAYS = config.HOLDOUT_DAYS


def main() -> int:
    df = data.load_all()
    boundary = data.holdout_boundary(df)
    cut = boundary - pd.Timedelta(days=HOLDOUT_DAYS)
    hold = df.loc[df.index > cut]

    out = data.HOLDOUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "btcusdt_1h_holdout.parquet"
    if dest.exists():
        print(f"holdout already sealed at {dest} — leaving it alone")
        return 0

    hold.to_parquet(dest)
    print(f"sealed {len(hold):,} bars  {hold.index.min()} -> {hold.index.max()}")
    print(f"boundary for training: {cut}")
    print(
        "\nIMPORTANT: this directory must not be mounted into any agent sandbox.\n"
        "The single permitted read is `make holdout`, which appends to ACCESS_LOG.txt."
    )

    # Sanity: the training slice must end strictly before the sealed window.
    train, boundary = data.load_train()
    assert train.index.max() < boundary, "train data overlaps the holdout boundary"
    assert hold.index.min() >= train.index.max(), "sealed window starts inside training"
    print(f"check: train ends {train.index.max()}, sealed starts {hold.index.min()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
