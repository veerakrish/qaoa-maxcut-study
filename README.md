# QAOA for MaxCut on small 3-regular graphs

An exact-simulation study of depth-p QAOA (p = 1, 2, 3) against classical baselines, on 64 unique connected cubic graphs
with 8 to 14 vertices. It is a methods exercise: formulate, implement, validate and evaluate a quantum optimisation
algorithm, with the success criteria fixed before the run ([docs/PREREGISTRATION.md](docs/PREREGISTRATION.md)).
It does not test quantum advantage, and the behaviour it reports is already known in the QAOA literature.

**Status: simulation phase only.** No hardware or noisy-simulation results exist yet.

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

## Validation

`python -m pytest` runs 26 tests. The ones that matter most:

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

1. Noisy simulation with a device noise model.
2. If a hardware phase follows, give it its own pre-registration. A natural question connects to the transpiler-seed variance
   found in the PhD work: does seed-to-seed variation in routed depth appear as variation in the measured approximation ratio?
   That is a hypothesis to test, not a finding.
