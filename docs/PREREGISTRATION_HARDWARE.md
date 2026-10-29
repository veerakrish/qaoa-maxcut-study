# Pre-registration: seed-level spread of QAOA results on IBM hardware

Written 2026-10-29, **before any hardware job exists** (the IBM API key was also invalid at the time of writing).
Commit this file before the first submission. Later changes go in the deviation log, never in place.
Context: [LITERATURE.md](LITERATURE.md) (this extends existing work and claims no novelty) and
[PREREGISTRATION.md](PREREGISTRATION.md) (the simulation phase).

## Question

For shallow QAOA on IBM hardware, how large is the seed-level spread of the measured approximation ratio, compared with
shot noise, device drift and the gain from one more QAOA layer? Does a calibration-based cost score pick better seeds than
Qiskit's fewest-swaps rule or a random seed? No quantum-advantage claim is made.

## Design

| Item | Choice |
|---|---|
| Instances | n = 8: all 5 graphs; n = 10: the first 5 graphs, both from `cubic_instances(n)` (the same deterministic enumeration as the simulation phase) |
| Depths | p = 1 and 2 |
| Parameters | the best restart (highest exact ratio) of the **ideal** arm for that graph and p from `results/raw`; not re-optimised on hardware |
| Compilation | `generate_preset_pass_manager(optimization_level=3, backend, seed_transpiler=s)` for s = 0..4, so five compiled circuits per (graph, p); Qiskit version and trial counts (20 at level 3) recorded |
| Circuits | 10 graphs x 2 depths x 5 seeds = 100, plus 10 repeats of one fixed compiled reference circuit (graph n=8 #0, p=1, seed 0) = **110 circuits**, 4096 shots each |
| Device and order | one 156-qubit Heron device chosen once, by shortest queue, for the whole batch; execution order randomised (fixed RNG seed); one job if the device allows it, otherwise the fewest jobs, with circuits assigned to jobs at random |
| Recorded at submission | backend name, calibration timestamp, per-gate error rates used by the cost score, job IDs, timestamps, compiled-circuit statistics |
| Cap | abort if the estimated QPU time exceeds 300 s or 50% of the remaining allowance; if the allowance is too small, run n = 8 only (60 circuits) and record the deviation |

Measured per circuit: mean cut of the sampled bitstrings divided by the exact maximum cut (approximation ratio r), the shot-noise
standard error, the compiled two-qubit gate count and depth, and the **cost score** F = product over two-qubit gates of (1 - gate error)
times product over measured qubits of (1 - readout error), from the calibration at submission (computed before running).

## Pre-flight gates (must pass before submission)

1. Every compiled circuit, simulated noiselessly on its active qubits, reproduces the ideal output distribution (total variation distance < 1e-6).
2. All circuits target the same backend and calibration snapshot; no seed is silently dropped; duplicate compiled circuits are kept as separate runs.
3. Estimated QPU time is within the cap, and the user has confirmed the exact backend, circuit count and estimate.

## Hypotheses and decision rules

- **HW1, a seed effect exists.** Per (graph, p) cell, S2 = sample variance of the five measured ratios. E2 = mean squared shot-noise
  standard error in that cell, plus the drift variance from the 10 reference repeats (their variance minus their mean squared standard error, floored at 0).
  R = mean(S2) / mean(E2) over cells, with a bootstrap 95% interval over cells. *Detected* if the lower bound of R exceeds 1; reported for p = 1, p = 2 and pooled.
- **HW2, spread against depth gain (descriptive).** Excess seed s.d. = sqrt(max(mean(S2) - mean(E2), 0)) against the per-graph
  difference in measured ratio between p = 2 and p = 1. "Comparable" is defined as the seed s.d. being at least half of the absolute mean difference.
  Reported either way, including whether p = 2 beats p = 1 on hardware at all.
- **HW3, the cost score predicts.** Within each cell, the Spearman correlation between F and the measured ratio across the five seeds; averaged over cells with a
  bootstrap interval over cells. *Predictive* if the lower bound is above 0.
- **HW4, selection rules.** Per cell, the measured ratio of the seed chosen by (a) fewest two-qubit gates (the proxy for Qiskit's fewest-swaps rule), (b) highest F,
  (c) the average over the five seeds (a random seed). Paired differences (b - c), (a - c) and (b - a), averaged over cells with bootstrap intervals.
  The cost score *helps* only if (b - c) has an interval above 0.
- **HW5, hardware against ideal (descriptive).** Measured ratio divided by the exact ideal ratio, by p.

All intervals are 95% percentile bootstrap over cells (10 cells per depth; 10,000 resamples, seed 0). No multiplicity correction. Null and negative outcomes are reported as results.

## Fixed in advance

No circuit or job is excluded after seeing data. A failed job is re-run once, and both attempts are reported. If the calibration timestamp changes during the batch,
both snapshots are reported and the one at submission is used for F. Every deviation goes in the log below.

## Known limitations

One device, one batch (one day), 10 graphs, 5 seeds per cell, so the cell-level estimates are noisy; 4096 shots; fixed rather than re-optimised parameters; the
cost score is a simple product of error rates, not a full noise model; hardware drift across the batch is estimated from one reference circuit only.

## Deviation log

(none yet)
