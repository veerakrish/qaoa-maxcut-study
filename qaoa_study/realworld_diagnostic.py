"""POST HOC, NOT PRE-REGISTERED. Why does r_best sometimes fall when p grows on the real-world graphs?

A depth-(p+1) QAOA contains the depth-p circuit (set the extra layer to gamma = beta = 0), so its optimum can never be lower.
A fall in r_best therefore means the random-start optimiser missed an optimum it could have reached. This warm-starts depth p+1 from the best
depth-p parameters plus an identity layer, then optimises with the same COBYLA budget.
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from .qaoa import QAOA

OUT = Path("results/realworld")


def warm(task):
    d = task
    model = QAOA(d["n"], [tuple(e) for e in d["edges"]])
    runs = [r for r in d["runs"] if r["mode"] == "ideal"]
    best = {p: max((r for r in runs if r["p"] == p), key=lambda r: r["ratio"]) for p in (1, 2, 3)}
    rows = []
    for p in (1, 2):
        x = np.array(best[p]["params"])
        x0 = np.concatenate([x[:p], [0.0], x[p:], [0.0]])
        start = model.expectation(x0) / model.cmax
        res = minimize(lambda v: -model.expectation(v), x0, method="COBYLA", tol=1e-4, options={"rhobeg": 0.3, "maxiter": 300})
        rows.append({"graph": d["name"], "step": f"p={p}->{p + 1}", "r_best(p) random start": best[p]["ratio"], "warm start value": start,
                     "warm start after optimising": -res.fun / model.cmax, "r_best(p+1) random start": best[p + 1]["ratio"]})
    return rows


def main() -> None:
    data = [json.loads(f.read_text()) for f in sorted((OUT / "raw").glob("*.json"))]
    with ProcessPoolExecutor() as pool:
        rows = [r for part in pool.map(warm, data) for r in part]
    lines = ["# Warm-start diagnostic (post hoc, not pre-registered)", "",
             "Warm start = best depth-p parameters plus an identity layer, then COBYLA with the same budget.", "",
             "| graph | step | r_best(p), random start | warm start value (must equal it) | after optimising | r_best(p+1), random start | optimiser missed by |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        missed = r["warm start after optimising"] - r["r_best(p+1) random start"]
        lines.append(f"| {r['graph']} | {r['step']} | {r['r_best(p) random start']:.4f} | {r['warm start value']:.4f} | "
                     f"{r['warm start after optimising']:.4f} | {r['r_best(p+1) random start']:.4f} | {missed:+.4f} |")
    bad = [r for r in rows if abs(r["warm start value"] - r["r_best(p) random start"]) > 1e-9]
    lines += ["", f"Identity-layer check (warm start value equals r_best(p)): {'PASS' if not bad else 'FAIL'}.",
              f"Steps where the random-start optimiser missed a higher value by more than 0.002: {sum(1 for r in rows if r['warm start after optimising'] - r['r_best(p+1) random start'] > 0.002)} of {len(rows)}."]
    text = "\n".join(lines)
    (OUT / "diagnostic.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
