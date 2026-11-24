# CODE_STYLE — The Fake Bitcoin Trap

## 1. Naming

| Thing | Convention | Example |
|---|---|---|
| Modules | `snake_case`, noun | `nulls.py`, `neff.py` |
| Functions | `snake_case`, verb | `deflate`, `block_bootstrap` |
| Classes | `PascalCase` | `TrialLog`, `Deflation` |
| Constants | `UPPER_SNAKE_CASE` | `BARS_PER_YEAR_HOURLY` |
| Frozen experiment values | in `config.py` only | `DSR_THRESHOLD` |
| Dataclass fields | `snake_case`, no prefixes | `n_eff` |

Short names are allowed where the maths is standard (`T`, `N`, `SR`, `lam`,
`pbo`). Do not invent new shorthand.

## 2. Formatting

- `ruff format` (line length 100) and `ruff check`.
- Imports: stdlib, third-party, local — three groups, one blank line between.
- `from __future__ import annotations` at the top of every module.
- No wildcard imports.

## 3. Types

- Annotate **every** public function signature, in and out.
- `np.ndarray` and `pd.Series` are annotated; do not fake arrays as `list`.
- Prefer `dataclass(frozen=True)` for records that must not be mutated
  (`Deflation`, `CostModel`, `NullSpec`).
- `Any` is not used. If a type is genuinely unknown, write the union.

## 4. Structure

- One responsibility per module, listed in `ARCHITECTURE.md`.
- Functions ≤ 40 lines. `engine.run` is the largest and is allowed to be longer
  because the record shape is the point.
- No module-level computation except constants. Importing a module must be
  free of side effects (no downloads, no file writes).
- `pipeline.py` orchestrates; it must not contain formulas.

## 5. The docstring rule (this project's most important rule)

Every statistic carries its formula in the docstring **above** the
implementation, in plain ASCII or LaTeX-ish notation, with the symbol
definitions. This is not decoration: the claim of the repository is that the
maths can be re-derived by hand, so the code must be checkable by inspection.

```python
def expected_max_sharpe(n_trials: float, sr_variance: float) -> float:
    """Analytic E[max] of n_trials iid Gaussian trial Sharpes, via Gumbel.

        E[max] ~ sqrt(V) * ((1-g) * Phi^-1(1 - 1/N) + g * Phi^-1(1 - 1/(N e)))

    V  : cross-trial variance of the (non-annualised) trial Sharpes
    g  : Euler-Mascheroni constant, 0.5772...
    """
```

## 6. Comments

Explain **why**, never **what**. Acceptable:

```python
# shift(1): the MA comparison at bar t is only knowable at the close of t.
```

Unacceptable:

```python
# compute the moving average
```

## 7. Errors

- Raise with the fixing command in the message:
  `FileNotFoundError("no klines in data/raw. Run: python scripts/download_data.py")`.
- Never `except Exception: pass`.
- A checksum mismatch is fatal for that month, reported on stderr, exit code 1.

## 8. Randomness

- Always `np.random.default_rng(seed)`; never the global `np.random`.
- Seeds derive from `(SEED, path_index, family)` so that increasing `N_PATHS`
  does not change earlier paths.

## 9. Git

Commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `data:` (download scripts
and manifests only), `chore:`.

Two special commits:
- `Freeze pre-registration` — must be the first commit touching `src/`.
- `RE-REGISTER: <what changed>` — required if `PREREGISTRATION.md` is edited
  after it was stamped. Bars may be sharpened, never loosened.
