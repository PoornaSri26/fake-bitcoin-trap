PY ?= python

.PHONY: help stamp data reproduce nulls trials neff dsr charts holdout clean test

help:
	@echo "make stamp      freeze + hash the pre-registration, then commit"
	@echo "make data       48 months of 1h klines from data.binance.vision"
	@echo "make reproduce  nulls -> agent trials -> N_eff -> DSR -> charts (no holdout)"
	@echo "make holdout    the single sealed read (requires authorisation)"
	@echo "make test       unit tests for the statistics"

stamp:
	$(PY) scripts/stamp_prereg.py

data:
	$(PY) scripts/download_data.py --months 60
	$(PY) scripts/seal_holdout.py

nulls:
	$(PY) -m btrap.pipeline nulls

trials:
	$(PY) -m btrap.pipeline trials

neff:
	$(PY) -m btrap.pipeline neff

dsr:
	$(PY) -m btrap.pipeline dsr

charts:
	$(PY) -m btrap.pipeline charts

reproduce: nulls trials neff dsr charts
	@echo "reproduced without touching the holdout."

holdout:
	BTRAP_RELEASE_HOLDOUT=1 $(PY) scripts/run_holdout.py

test:
	$(PY) -m pytest -q tests

clean:
	rm -rf outputs .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
