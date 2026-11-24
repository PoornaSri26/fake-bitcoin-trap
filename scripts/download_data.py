#!/usr/bin/env python
"""Download BTCUSDT 1h spot klines from data.binance.vision.

Verified layout (Nov 2026):

    https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/
        BTCUSDT-1h-YYYY-MM.zip  (+ .CHECKSUM)

The zip contains a single headerless CSV. NOTE: Binance switched SPOT
timestamps from milliseconds to *microseconds* for files from 2025-01-01
onwards, so a merged frame mixes units unless normalised. `btrap.data` handles
that; this script only downloads.

Usage:
    python scripts/download_data.py --months 60
    python scripts/download_data.py --months 60 --force
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

BASE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def month_seq(n: int, end: date | None = None) -> list[str]:
    end = end or date.today()
    out = []
    y, m = end.year, end.month - 1  # last complete month
    if m == 0:
        y, m = y - 1, 12
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return sorted(out)


def fetch(url: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def verify(payload: bytes, checksum_text: str, name: str) -> None:
    expected = checksum_text.split()[0].strip()
    got = hashlib.sha256(payload).hexdigest()
    if expected != got:
        raise RuntimeError(f"checksum mismatch for {name}: {expected} != {got}")


def download_month(month: str, force: bool = False) -> bool:
    name = f"BTCUSDT-1h-{month}.zip"
    dest = RAW / f"BTCUSDT-1h-{month}.csv"
    if dest.exists() and not force:
        print(f"  skip {month} (have {dest.name})")
        return True
    try:
        payload = fetch(f"{BASE}/{name}")
        cks = fetch(f"{BASE}/{name}.CHECKSUM").decode()
        verify(payload, cks, name)
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            inner = zf.namelist()[0]
            dest.write_bytes(zf.read(inner))
        print(f"  ok   {month}  {len(payload)/1e6:.1f} MB")
        return True
    except Exception as exc:  # noqa: BLE001 - report and continue
        print(f"  FAIL {month}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=60)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    months = month_seq(args.months)
    print(f"downloading {len(months)} months into {RAW}")
    ok = sum(download_month(m, args.force) for m in months)
    print(f"\n{ok}/{len(months)} months present")
    return 0 if ok == len(months) else 1


if __name__ == "__main__":
    raise SystemExit(main())
