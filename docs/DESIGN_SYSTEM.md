# DESIGN_SYSTEM — The Fake Bitcoin Trap

The visual output of this project is **two figures and a set of tables**. They
are read by a quant who will look for the axis units first and the story second.
The design system exists so that every figure is legible in a PDF, in a GitHub
README and on a phone.

## 1. Colour tokens

Single-hue, colour-blind-safe. Never encode a category by hue alone.

| Token | Hex | Use |
|---|---|---|
| `ink` | `#111318` | text, axes |
| `grid` | `#D6DAE1` | gridlines (0.6 pt, alpha 0.7) |
| `empirical` | `#3B6EA5` | measured / Monte Carlo series |
| `analytic` | `#1B1F26` | closed-form series (dashed) |
| `pass` | `#2E7D32` | at or above the bar |
| `fail` | `#B3261E` | below the bar |
| `muted` | `#6B7280` | annotations, secondary notes |

Rules:
- At most **two** coloured series per panel; the rest are ink/muted.
- The bar (0.95 or a Sharpe threshold) is always a **dashed horizontal line**
  with its value written at the right end. No legend entry for it.
- Never use a rainbow or a jet colormap. If a heatmap is needed, use a single-hue
  ramp from `#F3F6FA` to `#1B4F8A`.

## 2. Figure geometry

| Property | Value |
|---|---|
| Size | 7.0 × 4.5 in (single), 6.0 × 4.0 in (bar chart) |
| DPI | 160 for PNG, 300 for print |
| Font | system sans (`DejaVu Sans` fallback), 9 pt ticks, 11 pt title |
| Line width | 1.4 pt series, 0.6 pt grid |
| Markers | 3 pt, only on the empirical curve |
| Spines | top/right removed |
| Background | white, no figure frame |

## 3. Axis conventions

- **X (trials):** log scale, ticks at 1/10/100/1000, label `trials N`.
- **Y (Sharpe):** annualised, label `annualised Sharpe`, always crosses zero.
- **Y (probability/DSR):** 0-1, ticks every 0.25, bar at 0.95 drawn.
- Every axis label states the **unit** (`bp`, `ticks`, `annualised`). No bare
  numbers.

## 4. Required annotations

Every figure ships with:
1. the number of trials or paths it is based on (`n=200 paths`, `N=120 trials`);
2. the seed family if it is a simulation;
3. one sentence in the title stating the *conclusion*, not the variable name
   ("what luck alone buys you", not "Sharpe vs trials").

## 5. Tables

- Numbers right-aligned, three decimals for ratios, two for percentages.
- The pass/fail row is bolded, not coloured (colour is unreliable in print).
- Column order: identifier, sample size, point estimate, interval, verdict.

## 6. Implementation

`src/btrap/plotting.py` holds the tokens and an `apply_style()` that
`pipeline.stage_charts` calls before drawing. If a token is missing, add it
there — never hard-code a hex value inside a plotting function.

## 7. Accessibility checklist

- [ ] Greyscale test: the figure is still readable with all colour removed.
- [ ] Contrast of ink on white ≥ 7:1; muted text ≥ 4.5:1.
- [ ] No information is carried by colour alone (dash style or marker too).
- [ ] Text ≥ 9 pt at 160 dpi.
- [ ] The alt text in the README states the conclusion, not "chart 1".
