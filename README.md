# QAOA for MaxCut on small 3-regular graphs

An exact-simulation study of depth-p QAOA (p = 1, 2, 3) against classical baselines, on 64 unique connected cubic graphs
with 8 to 14 vertices. It is a methods exercise: formulate, implement, validate and evaluate a quantum optimisation
algorithm, with the success criteria fixed before the run ([docs/PREREGISTRATION.md](docs/PREREGISTRATION.md)).
It does not test quantum advantage, and the behaviour it reports is already known in the QAOA literature.

**Status:** the simulation phase is complete, and one pre-registered hardware batch has been run (110 circuits on `ibm_marrakesh`,
2026-10-29). No noisy-simulation results exist.

## Results

Full tables, intervals and per-hypothesis verdicts: [results/summary.md](results/summary.md). Figures: `figures/`.
All intervals are 95% bootstrap over graphs (5 graphs at n = 8, 19 at n = 10, 20 at n = 12 and 14).

| n | QAOA p=1 | p=2 | p=3 (best of 5 restarts) | Goemans-Williamson, single rounding | 1-flip local search, single run | random cut |
|---|---|---|---|---|---|---|
| 8 | 0.783 | 0.868 | 0.910 | 0.977 | 0.970 | 0.580 |
| 10 | 0.786 | 0.866 | 0.904 | 0.961 | 0.967 | 0.581 |
| 12 | 0.779 | 0.856 | 0.895 | 0.954 | 0.958 | 0.576 |
| 14 | 0.782 | 0.855 | 0.896 | 0.954 | 0.957 | 0.581 |

Approximation ratio = expected cut / maximum cut. QAOA values are exact expectations at the optimised parameters.

| Hypothesis (pre-registered) | Outcome |
|---|---|
| H1: depth helps, p=1 to 2 to 3 | **Supported** at every size and step (gains about +0.07 to +0.09, then +0.04) |
| H2: QAOA stays below single-run classical baselines | **As expected**: p=3 is 0.06 to 0.07 below both at every size. No advantage |
| H3: shot noise lowers quality | **Not supported at every cell**: it fails at (n=8, p=1) and (n=14, p=1), where the interval includes 0. At p = 2 and 3 the shots arm is 0.05 to 0.11 lower, but this is confounded with early stopping (below) |
| H4: P(optimal cut) and best-of-shots | Descriptive; see below |

Things worth knowing before reading these numbers:

- **The shot-limited arm does not benefit from depth.** Its ratio stays near 0.75 to 0.79 for p = 1, 2 and 3.
  COBYLA ends that arm after about 30 to 60 evaluations (the exact arm uses up to 300), so shot noise and early
  stopping are confounded; this study cannot say how much of the gap is each. An optimiser built for noisy objectives
  (for example SPSA) was not tested.
- **P(optimal cut) falls with size.** At p = 3 it is 0.58 (n=8), 0.39 (n=10), 0.24 (n=12) and 0.20 (n=14). The large gains over
  uniform sampling (30x to 733x) come mostly from the uniform probability shrinking as 2^-n.
- **Best-of-1024-shots gives no advantage.** QAOA reaches the maximum cut at every size, but so do Goemans-Williamson roundings
  (1.000) and local search (0.999 to 1.000 with 10 restarts). Uniform random sampling already reaches 0.995 at n = 10 and 0.949 at n = 14.
- **Small, single-family study.** Exact simulation, n <= 14, unweighted cubic graphs, no hardware noise, one optimiser.

## Hardware results (one batch, one device, one day)

Design, decision rules and cost cap: [docs/PREREGISTRATION_HARDWARE.md](docs/PREREGISTRATION_HARDWARE.md), committed before the
job was submitted. 10 graphs (n = 8 and 10), p = 1 and 2, 5 transpiler seeds each (optimisation level 3), plus 10 repeats of one
reference circuit to measure drift: 110 circuits at 4096 shots in a single job on `ibm_marrakesh` (job `dbhhjscdgr2s73ctigs0`,
126 s of QPU time, calibration unchanged during the batch). Full output: [results/hardware/summary.md](results/hardware/summary.md).

| Pre-registered question | Outcome |
|---|---|
| HW1: seed-level spread beyond shot noise and drift? | **Detected.** Seed variance is 11x the shot-noise-plus-drift level (95% CI 4.6 to 20); excess seed s.d. about 0.008 in a ratio near 0.77. The device was stable (reference-circuit s.d. 0.0025, close to the shot-noise 0.0023) |
| HW2: comparable to the gain from one more layer? | **No.** p = 2 beat p = 1 by +0.034 (95% CI 0.026 to 0.041), about four times the seed s.d., although noise removes more than half of the ideal gain |
| HW3: does the calibration-based cost score rank seeds? | **Not shown.** Mean within-graph Spearman correlation -0.13 (95% CI -0.41 to 0.15) |
| HW4: does choosing by that score beat a random seed? | **No** (difference -0.0008, 95% CI -0.0032 to 0.0017). Choosing the seed with the fewest two-qubit gates did slightly better than random (+0.0030, CI 0.0001 to 0.0067, uncorrected for three comparisons) |
| HW5: hardware against ideal | Measured / ideal ratio 0.96 at p = 1 and 0.90 at p = 2 |

Post-hoc checks ([results/hardware/exploratory.md](results/hardware/exploratory.md), **not pre-registered**): across all circuits the score is
well calibrated as a predictor of the drop from the ideal ratio (slope 0.99, R^2 0.71) but explains nothing within a graph (slope 0.09, R^2 0.00);
two-qubit gate count ranks seeds better (Spearman -0.31, CI -0.48 to -0.13); 42% of the seed variance sits in one cell (n = 8, graph 4, p = 2)
and 65% in three, yet dropping any single cell leaves the effect (R 8 to 14) and 17 of 20 cells exceed twice their shot-noise variance.

Caveats: one device and one day; 20 cells of 5 seeds, so the rank-correlation interval is wide (the score may carry a signal this design could not resolve);
the "seed" effect is any difference between compiled circuits (different physical qubits and gate counts), not randomness as such;
parameters were fixed from the noiseless optimum, not tuned on hardware; the analysis code was committed after submission but before any result existed.

## Real-world networks (simulation)

Seven small instances from real networks that ship inside networkx (Zachary's karate club, Padgett's Florentine families, Knuth's Les Miserables,
the Southern women network), cut to 15 or 16 nodes by two rules fixed in advance: [docs/PREREGISTRATION_REALWORLD.md](docs/PREREGISTRATION_REALWORLD.md).
Same protocol as above, exact simulation. Per-graph output: [results/realworld/summary.md](results/realworld/summary.md).

| Graph | n | edges | QAOA p=1 | p=2 | p=3 | Goemans-Williamson (single) | local search (single) |
|---|---|---|---|---|---|---|---|
| Florentine families | 15 | 20 | 0.657 | 0.858 | 0.900 | 0.965 | 0.945 |
| karate club, core-16 | 16 | 39 | 0.830 | 0.830 | 0.912 | 0.968 | 0.950 |
| karate club, ball-16 | 16 | 28 | 0.747 | 0.821 | 0.800 * | 0.982 | 0.906 |
| Les Miserables, core-16 | 16 | 67 | 0.818 | 0.904 | 0.881 * | 0.951 | 0.942 |
| Les Miserables, ball-16 | 16 | 33 | 0.848 | 0.891 | 0.890 | 0.972 | 0.963 |
| Southern women, core-16 (bipartite) | 16 | 39 | 0.508 | 0.644 | 0.771 | 1.000 | 0.944 |
| Southern women, ball-16 (bipartite) | 16 | 17 | 0.688 | 0.792 | 0.848 | 1.000 | 0.944 |

`*` marks a fall with depth that no true optimum can show (see below).

- **RW1, depth helps:** holds on 5 of 7 graphs as pre-registered. The two exceptions are optimiser misses, not physics: a depth-3 circuit contains the depth-2
  circuit, so its optimum cannot be lower. A post-hoc warm-start check ([results/realworld/diagnostic.md](results/realworld/diagnostic.md), not pre-registered)
  reaches 0.863 on karate ball-16 and 0.921 on Les Miserables core-16, above both the random-start values and the depth-2 values. The 64-graph cubic study shows no such fall (0 of 128 steps).
- **RW2, classical baselines:** QAOA at p = 3 is below both single-run baselines on all 7 graphs. No advantage.
- **RW3/RW4, structure matters:** the dense Les Miserables core leaves little headroom (a random cut already reaches 0.80; QAOA at p = 1 adds only +0.020). The bipartite
  Southern-women graphs sit below the cubic-graph range at every depth although classical methods are exact there (p = 1 is only +0.008 over random on the core graph).
  Four of seven graphs are inside the cubic-graph range at p = 3; karate ball-16 (an optimiser miss) and the two bipartite graphs are below it.
- **Caveats:** seven graphs of at most 16 vertices, two arbitrary selection rules, unweighted, ideal simulation, one optimiser. Nothing generalises beyond these instances.

## Validation

`python -m pytest` runs 28 tests (26 for the simulator and baselines, 2 for the hardware analysis on synthetic data). The ones that matter most:

- the numpy simulator agrees with an independent Qiskit statevector to 1e-10 (p = 1, 2, 3, several graphs);
- the single-edge closed form, and the ring-graph p = 1 value of 3/4;
- on every triangle-free cubic graph the p = 1 optimum is the same constant, 0.6924 of the edges
  (Farhi, Goldstone, Gutmann 2014), which the study's own results reproduce on all 11 such graphs (spread 2e-9),
  while graphs with triangles fall lower (0.647 to 0.685);
- exact enumeration of all 5 and 19 connected cubic graphs on 8 and 10 vertices;
- baseline checks: SDP value 9/4 for the triangle, SDP >= exact maximum cut on every graph, local search ends at a 1-flip optimum.

## Reproduce

```bash
pip install -r requirements.txt
python -m pytest                       # about 20 s
python -m qaoa_study.experiment        # about 8 min on 7 workers; resumable, one JSON per graph in results/raw
python -m qaoa_study.analysis          # writes results/summary.md, results/summary.csv and figures/
python -m qaoa_study.realworld_run     # real-world networks, about 10 min; results/realworld/
```

Everything is seeded; the configuration used is in `results/config.json`.

## Layout

```
qaoa_study/graphs.py      instances (unique connected cubic graphs) and exact MaxCut
qaoa_study/qaoa.py        exact statevector QAOA, sampling
qaoa_study/circuit.py     the same QAOA as a Qiskit circuit (cross-check; entry point for hardware work)
qaoa_study/classical.py   Goemans-Williamson (low-rank SDP + rounding), 1-flip local search
qaoa_study/experiment.py  the pre-registered protocol
qaoa_study/analysis.py    the pre-registered decision rules
docs/PREREGISTRATION.md   criteria written before the full run, with a deviation log
```

## Limitations

- The Goemans-Williamson value comes from a local low-rank solver, not a certified SDP solve (it is checked against the exact maximum on every graph).
- Random-start protocol only; no structured initialisation, which is known to help at larger p.
- The pre-registration file was saved at 14:57:09 and the first result at 14:57:46 on 2026-10-29 (file timestamps).
  The repository has no commits yet, so git history does not yet show the order; commit the pre-registration and the code
  before the results if you want the history to carry that evidence.

## Provenance and AI assistance

This repository was scaffolded with AI assistance (Claude Code). [Author: describe what you read, changed and ran yourself
before publishing, and which parts you can explain in detail.]

## Next steps (not done)

1. Replicate on a second device and day with more seeds per graph, which is the main limit of the batch above.
2. Ask why gate count ranks seeds while the calibration-based score does not (representativeness of reported error rates, crosstalk, or low power);
   any follow-up gets its own pre-registration.
3. Compare against mapomatic itself, and test larger instances.
