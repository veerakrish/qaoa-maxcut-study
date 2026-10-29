# Pre-registration: QAOA for MaxCut on small 3-regular graphs (simulation phase)

Written 2026-10-29, **before the full experiment was run**. Commit this file before reading any results, so the
history shows the criteria came first. Changes after the full run go in the deviation log at the bottom, never in place.

## Purpose and non-goals

Measure how well depth-p QAOA solves MaxCut on small cubic graphs, against standard classical baselines, using exact
simulation. The aim is to formulate, implement and evaluate a quantum optimisation algorithm rigorously.
It is **not** a test of quantum advantage and makes no novelty claim; nothing here is expected to beat the classical baselines.

## Design

| Item | Choice |
|---|---|
| Instances | unique, non-isomorphic, connected 3-regular graphs; n = 8 (all 5), 10 (all 19), 12 (20 of 85), 14 (20 of 509); unweighted |
| Statistical unit | the graph (restarts and shots are nested inside it) |
| Algorithm | standard QAOA, p = 1, 2, 3; objective <C> = expected number of cut edges; conventions in `qaoa_study/qaoa.py` |
| Simulation | exact statevector in numpy, cross-checked against Qiskit (`tests/test_qaoa.py`); no hardware noise |
| Optimiser | COBYLA, rhobeg 0.3, tol 1e-4, at most 300 evaluations; 5 independent random starts per (graph, p), gamma ~ U(0, pi), beta ~ U(0, pi/2) |
| Arms | **ideal**: exact <C> as objective. **shots**: objective is the mean cut of 1024 sampled shots per evaluation |
| Final evaluation | the exact <C> and P(optimal cut) at the returned parameters (for both arms); best cut among 1024 further shots |
| Baselines | random cut (<C> = half the number of edges); Goemans-Williamson rounding of a low-rank SDP solution (1024 roundings); 1-flip local search from random starts (200 runs); uniform random sampling with the same 1024 shots |
| Primary metric | approximation ratio r = <C> / C_max, with C_max from exhaustive enumeration |
| Uncertainty | percentile bootstrap over graphs, 10,000 resamples, seed 0; 95% intervals; no multiplicity correction (descriptive) |

Per graph and p, `r_best` is the maximum over the 5 restarts of the exact ratio (the ideal arm has the exact objective,
so a practitioner could make this choice); `r_mean` is the mean over restarts. The shots arm is summarised by `r_mean` only,
because a practitioner could not select restarts by the exact value.

## Hypotheses and decision rules

- **H1, depth helps.** On the ideal arm, `r_best` increases from p = 1 to 2 and from 2 to 3. For each n the paired
  per-graph differences have a 95% interval above 0. *Supported* only if this holds for both steps at every n; otherwise
  report exactly which n and step fail. The same is reported for `r_mean` as a robustness check.
- **H2, classical baselines.** The expected outcome is that p = 3 QAOA stays *below* the single-run Goemans-Williamson
  rounding and the single-run local search at every n (paired intervals, `r_best` and `r_mean`). If QAOA is not below a baseline, treat it as a
  possible bug first (re-run the validation gates) and report it with the caveat that n <= 14 and the baselines are
  single runs. No advantage claim is made either way.
- **H3, shot noise costs quality.** On `r_mean`, the shots arm is below the ideal arm at each (n, p) (paired interval
  below 0). The comparison is of COBYLA's own stopping rule in each arm: on a noisy objective COBYLA stops after roughly
  50-120 evaluations, the ideal arm often uses 300, so shot noise and early stopping are confounded. Evaluations and shots
  used are reported next to the ratios.
- **H4, descriptive only.** The factor by which QAOA at p = 3 raises P(optimal cut) over uniform sampling (n_opt / 2^n),
  and the best-of-1024-shots ratio of QAOA against uniform random sampling with the same shots. At n <= 10 the uniform
  baseline is expected to be near saturation, so best-of-shots comparisons there carry little information.

## Validation gates (must hold before any result is reported)

1. `python -m pytest` passes: agreement with Qiskit to 1e-10, the single-edge closed form, the ring-graph p = 1 value of 3/4,
   periodicity and symmetry, exact instance enumeration (5 and 19 graphs), SDP and local-search checks.
2. For every graph the SDP value from the low-rank solver is at least the exact maximum cut (checked in `baselines()`; the run aborts otherwise).
3. No run has ratio > 1 + 1e-9, and no graph is duplicated within a size.

## Known limitations fixed in advance

Exact simulation and no hardware noise; n <= 14; one graph family (unweighted cubic); one optimiser, whose shots-arm
behaviour is described above (an optimiser designed for noisy objectives, such as SPSA, is not tested); random-start
protocol, not a structured initialisation; the Goemans-Williamson value comes from a local low-rank solver, not a
certified SDP solve.

## Deviation log

- 2026-10-29 (before the full run): a smoke test on 4 tiny tasks (n = 8 and 14, 2 graphs, p = 1 and 3, 1 restart; ratios not
  examined) showed that COBYLA ends the shots arm after 50-120 evaluations regardless of tolerance. An attempt to force
  an equal budget with a tiny tolerance did not work, so the protocol keeps COBYLA's own stopping rule and records evaluations used (see H3).
