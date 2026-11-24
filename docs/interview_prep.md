# Interview prep — what to be able to derive on a whiteboard

No AI. Paper only. Each item is a 5–10 minute derivation.

## 1. Expected maximum of N Gaussians (the Gumbel route)

Let $X_1..X_N \sim N(0,V)$. Then $M_N = \max_i X_i$. For large $N$,

$$P(M_N \le x) \approx \exp\left(-N\,\bar\Phi(x)\right)$$

Fixing the level so that $N\bar\Phi(x)$ is $O(1)$ and expanding $\bar\Phi$ via
Mills' ratio gives the Gumbel location and scale. The resulting expectation is

$$E[M_N] \approx \sqrt{V}\left[(1-\gamma)\Phi^{-1}\!\left(1-\tfrac1N\right) + \gamma\,\Phi^{-1}\!\left(1-\tfrac{1}{Ne}\right)\right]$$

with $\gamma = 0.5772$. **Be able to say why the leading term is $\sqrt{2V\ln N}$**: the two-parameter form above is a refinement of that.

## 2. Why correlation shrinks N

Trial Sharpes are not independent. If the trial return series have covariance
$\Sigma$ with eigenvalues $\lambda_i$, the number of *effectively independent*
directions is

$$N_{\text{eff}} = \frac{(\sum_i \lambda_i)^2}{\sum_i \lambda_i^2}$$

and the deflation should use $N_{\text{eff}}$ in the Gumbel formula with the
same variance. Intuition: highly correlated trials share their luck, so a
maximum over 100 correlated trials is much closer to a maximum over ~5.

Say explicitly that clustering (ONC) and the participation ratio estimate the
same quantity differently, and that reporting both is the honest move.

## 3. Why the DSR cannot detect leakage

DSR asks: *given this N and this return distribution, how surprising is this
Sharpe?* Leakage produces a Sharpe that is genuinely large **and** a
distribution of returns that looks fine (low skew, normal-ish kurtosis). There
is nothing in the (SR, skew, kurtosis, T, N) tuple that encodes "the feature was
computed with future information". Hence: DSR ≥ 0.95 is necessary, never
sufficient. The sealed holdout is the only check that can catch it, which is
why it must be read once.

## 4. Probabilistic Sharpe Ratio

Derive the standard error of $\hat{SR}$ under iid returns with skew $g_3$ and
kurtosis $g_4$:

$$\widehat{SE}(\hat{SR}) = \sqrt{\frac{1 - g_3 \hat{SR} + \frac{g_4-1}{4}\hat{SR}^2}{T-1}}$$

Then $PSR(SR^*) = \Phi\!\left((\hat{SR}-SR^*)/\widehat{SE}\right)$. Explain the
sign of the skew term: negative skew inflates the SE, so the same Sharpe is
less trustworthy.

## 5. Why PBO and DSR disagree

PBO is about the *selection procedure across time halves*; DSR is about the
*number of tries*. A strategy can have a high DSR and a bad PBO (good in
aggregate, unstable across halves). Present both and say which one the bar was
set on.

## 6. Questions to expect

- "You ran 120 trials. Why is the threshold not just $1.96/\sqrt{120}$?" —
  because trial Sharpes are correlated and the max of a correlated family is
  not the max of 120 independent tests; the Gumbel route with $N_{\text{eff}}$
  is the correction, and the null panel is the empirical check on it.
- "Your N_eff is 4.2 from a participation ratio and 11 from clustering. Which
  do you believe?" — the one that makes the test harder, and show both.
- "How would you have detected leakage?" — holdout, plus a synthetic test: plant
  a feature computed from $t+1$ and confirm the harness's DSR does *not* flag
  it while the holdout does. That is the falsification test for the instrument.
