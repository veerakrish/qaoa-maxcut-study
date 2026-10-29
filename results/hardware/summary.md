# Hardware results (pre-registered analysis)

110 circuits (20 cells x 5 seeds, plus 10 reference repeats). Intervals are 95% bootstrap over cells (graphs for HW2).

## HW1: is there a seed-level effect beyond shot noise and drift?

**Pooled verdict: DETECTED.** Drift variance from the reference repeats: 8.84e-07 (reference repeats: mean r = 0.7605, s.d. = 0.0025, mean shot-noise s.e. = 0.0023).

| cells | mean seed variance | mean expected (shot noise + drift) | R [95% CI] | seed effect detected (lower bound > 1) |
|---|---|---|---|---|
| p = 1 | 2.59e-05 | 5.91e-06 | 4.38 [2.48, 7.26] | yes |
| p = 2 | 1.14e-04 | 6.59e-06 | 17.31 [5.71, 30.60] | yes |
| pooled | 7.00e-05 | 6.25e-06 | 11.20 [4.62, 20.08] | yes |

## HW2: seed spread against the depth gain (descriptive)

Excess seed s.d. = 0.0080. Measured ratio at p = 2 minus p = 1, per graph: mean 0.0335 [0.0261, 0.0411] (10 graphs). **Seed spread is smaller than half of the depth gain** (rule: seed s.d. >= 0.5 x |mean difference|). p = 2 beats p = 1 on hardware.

## HW3: does the cost score predict the measured ratio across seeds?

Mean within-cell Spearman correlation -0.132 [-0.409, 0.149] (0 cells with constant scores dropped). **NOT shown to be predictive** (lower bound not > 0).

## HW4: selection rules

**The cost score is NOT shown to help over a random seed** (needs (b - c) above 0).

| comparison | mean difference in measured ratio [95% CI] | interval above 0 |
|---|---|---|
| cost score vs random seed (b - c) | -0.0008 [-0.0032, 0.0017] | no |
| fewest two-qubit gates vs random seed (a - c) | 0.0030 [0.0001, 0.0067] | yes |
| cost score vs fewest two-qubit gates (b - a) | -0.0039 [-0.0077, -0.0006] | no |

## HW5: hardware against ideal (descriptive)

| n | p | mean measured ratio | mean ideal ratio | measured / ideal | mean cost score F |
|---|---|---|---|---|---|
| 8 | 1 | 0.749 | 0.783 | 0.956 | 0.836 |
| 8 | 2 | 0.785 | 0.868 | 0.904 | 0.760 |
| 10 | 1 | 0.760 | 0.795 | 0.956 | 0.784 |
| 10 | 2 | 0.790 | 0.870 | 0.908 | 0.683 |

For reference, a uniformly random cut has ratio about 0.58 on these graphs.
