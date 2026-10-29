# Pre-registration: QAOA MaxCut on small real-world networks (simulation)

Written 2026-10-29, **before QAOA was run on these instances**. Only their sizes were looked at (to check they were usable).
Same protocol as [PREREGISTRATION.md](PREREGISTRATION.md); deviations go in the log at the bottom.

## Why

The simulation study used random cubic graphs. This asks whether the same behaviour holds on graphs from real data, which have uneven
degrees, hubs and (for the Davis network) a bipartite structure. It is a small descriptive check, not a benchmark.

## Instances (no download; the datasets ship inside networkx; edge weights dropped; unweighted MaxCut)

| Network | Rule | Instances |
|---|---|---|
| Padgett, Florentine families | whole network (largest component) | 1 (n = 15) |
| Zachary, karate club (1977) | **core-16**: induced subgraph on the 16 highest-degree nodes (ties by name), largest component; **ball-16**: first 16 nodes of a breadth-first search from the highest-degree node | 2 |
| Knuth, Les Miserables co-appearances (1993) | core-16 and ball-16, as above | 2 |
| Davis, Gardner, Gardner, Southern women (1941; bipartite) | core-16 and ball-16, as above | 2 |

Seven instances, n = 15 or 16, 17 to 67 edges, all connected (`qaoa_study/realworld.py`). Two selection rules are used and both are reported; the rules were
fixed before any QAOA run. Weights, direction and community labels are ignored.

## Protocol

As in the simulation study: standard QAOA, p = 1, 2, 3; COBYLA (rhobeg 0.3, tol 1e-4, at most 300 evaluations); five random starts per (graph, p);
exact expectation as the objective (the ideal arm only); ratio = <C> / C_max with C_max by enumeration. Baselines: random cut, Goemans-Williamson (single
rounding and best of 1024), 1-flip local search (single run and best of 10). Seven graphs are too few for bootstrap intervals, so results are reported **per graph**.

## Decision rules (per graph, then counted)

- **RW1, depth.** `r_best` is non-decreasing from p = 1 to 2 to 3 within a tolerance of 0.002. Reported as the number of graphs for which this holds, listing exceptions.
- **RW2, classical baselines.** At p = 3, `r_best` is below both the single-run Goemans-Williamson ratio and the single-run local-search ratio. Reported as a count;
  graphs where QAOA is not below are re-checked for bugs first. On the two bipartite graphs the optimum cuts every edge, so classical methods are expected to reach 1.
- **RW3, against cubic graphs (descriptive).** For each real graph and p, whether `r_best` falls below, inside or above the range (min to max) of `r_best` over the 64 cubic graphs of the simulation study.
- **RW4, descriptive.** P(optimal cut) at p = 3 against uniform sampling, and the advantage of QAOA at p = 1 over the random-cut ratio.

## Validation gates

SDP value >= exact maximum cut on every graph; no ratio above 1 + 1e-9; the test suite passes.

## Limitations fixed in advance

Seven graphs of at most 16 vertices; subgraph selection is by two arbitrary but declared rules, so these are samples from real networks, not the networks themselves;
unweighted; exact simulation, no noise or hardware; one optimiser. Nothing here generalises beyond these instances.

## Deviation log

- 2026-10-29: no deviation from the protocol. RW1 held on 5 of 7 graphs as pre-registered. Because a fall with depth is impossible for a true optimum, a post-hoc warm-start
  diagnostic (`qaoa_study/realworld_diagnostic.py`, not pre-registered) was added afterwards. It shows the two exceptions are optimiser misses. The RW1 count above stands as reported.
