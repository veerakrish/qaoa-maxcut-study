# Exploratory checks (post hoc, not pre-registered)

## 1. Calibration of the cost score
A depolarising reading of the score predicts the drop from the ideal ratio as (1 - F) x (ideal ratio - random-cut ratio). Slope 1 would mean calibrated.

- Across all 100 circuits: slope 0.99, R^2 0.71.
- Within cells (seed-to-seed differences only): slope 0.09, R^2 0.00.

## 2. Within-cell rank correlation with the measured ratio

- two-qubit gate count: mean within-cell Spearman correlation with the measured ratio -0.306 (95% CI -0.479 to -0.133)
- two-qubit depth: mean within-cell Spearman correlation with the measured ratio -0.099 (95% CI -0.279 to 0.086)
- cost score F: mean within-cell Spearman correlation with the measured ratio -0.132 (95% CI -0.409 to 0.149)

## 3. Concentration of the seed effect
- Largest cell: n=8, graph 4, p=2, seed s.d. 0.0243, 42% of the total seed variance; top 3 cells carry 65%.
- Pooled R (shot-noise-only denominator) after dropping any single cell: 8.3 to 13.8 (all cells: 13.0).
- Cells whose seed variance exceeds twice their shot-noise variance: 17 of 20.
