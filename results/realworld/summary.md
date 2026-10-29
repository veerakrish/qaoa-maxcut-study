# Real-world networks: results

7 instances, QAOA p = 1-3, five restarts each, exact simulation. Per-graph results only (too few graphs for intervals). Decision rules: `docs/PREREGISTRATION_REALWORLD.md`.

## Validation gates

- PASS: SDP value >= exact maximum cut and no ratio above 1 on every graph

## Per graph

| graph | n | edges | bipartite | r_best p=1 | p=2 | p=3 | r_mean p=3 | GW single | local search single | random cut | RW1 non-decreasing | RW2 below both | RW3 vs cubic (p=1/2/3) | RW4 P(opt) p=3 | RW4 p=1 minus random |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| florentine_families (whole network, largest component) | 15 | 20 | no | 0.657 | 0.858 | 0.900 | 0.849 | 0.965 | 0.945 | 0.588 | yes | yes | below/inside/inside | 0.188 (616x uniform) | +0.069 |
| karate_club core-16 | 16 | 39 | no | 0.830 | 0.830 | 0.912 | 0.839 | 0.968 | 0.950 | 0.696 | yes | yes | inside/inside/inside | 0.112 (305x uniform) | +0.134 |
| karate_club ball-16 | 16 | 28 | no | 0.747 | 0.821 | 0.800 | 0.780 | 0.982 | 0.906 | 0.609 | NO | yes | inside/inside/below | 0.046 (95x uniform) | +0.138 |
| les_miserables core-16 | 16 | 67 | no | 0.818 | 0.904 | 0.881 | 0.845 | 0.951 | 0.942 | 0.798 | NO | yes | inside/inside/inside | 0.005 (16x uniform) | +0.020 |
| les_miserables ball-16 | 16 | 33 | no | 0.848 | 0.891 | 0.890 | 0.801 | 0.972 | 0.963 | 0.717 | yes | yes | inside/inside/inside | 0.056 (77x uniform) | +0.131 |
| davis_southern_women core-16 | 16 | 39 | yes | 0.508 | 0.644 | 0.771 | 0.686 | 1.000 | 0.944 | 0.500 | yes | yes | below/below/below | 0.238 (7801x uniform) | +0.008 |
| davis_southern_women ball-16 | 16 | 17 | yes | 0.688 | 0.792 | 0.848 | 0.818 | 1.000 | 0.944 | 0.500 | yes | yes | below/below/below | 0.349 (11446x uniform) | +0.188 |

## Verdicts

- **RW1** (non-decreasing in p within 0.002): holds on 5 of 7 graphs.
- **RW2** (p = 3 below both single-run classical baselines): holds on 7 of 7 graphs.
- **RW3**: range of `r_best` over the 64 cubic graphs: p=1: 0.692 to 0.866; p=2: 0.792 to 0.925; p=3: 0.851 to 0.967.
