"""POST HOC, NOT PRE-REGISTERED. Descriptive robustness checks run after the pre-registered hardware analysis had been seen.

Nothing here changes a pre-registered verdict. Results are written to results/hardware/exploratory.md and labelled as exploratory.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from .analysis_hardware import OUT, bootstrap, load_runs
from .hardware import instances


def main() -> None:
    runs = load_runs()
    edges = {(i["n"], i["graph"], i["p"]): i["edges"] for i in instances()}
    cells: dict = {}
    for r in runs:
        if not r["repeat"]:
            cells.setdefault(tuple(r["key"][:3]), []).append(r)
    keys = sorted(cells)
    out = ["# Exploratory checks (post hoc, not pre-registered)", ""]

    # 1. Is the pre-registered cost score calibrated, on average and within a cell?
    drop, model, cdrop, cmodel = [], [], [], []
    for k in keys:
        rs = cells[k]
        random_ratio = len(edges[k]) / 2 / rs[0]["cmax"]
        d = np.array([r["ideal_ratio"] - r["r"] for r in rs])
        m = np.array([(1 - r["fidelity_score"]) * (r["ideal_ratio"] - random_ratio) for r in rs])
        drop.append(d)
        model.append(m)
        cdrop.append(d - d.mean())
        cmodel.append(m - m.mean())
    drop, model, cdrop, cmodel = (np.concatenate(x) for x in (drop, model, cdrop, cmodel))
    slope, slope_c = float(drop @ model / (model @ model)), float(cdrop @ cmodel / (cmodel @ cmodel))
    r2 = float(np.corrcoef(drop, model)[0, 1] ** 2)
    r2_c = float(np.corrcoef(cdrop, cmodel)[0, 1] ** 2)
    out += ["## 1. Calibration of the cost score",
            "A depolarising reading of the score predicts the drop from the ideal ratio as (1 - F) x (ideal ratio - random-cut ratio). Slope 1 would mean calibrated.", "",
            f"- Across all 100 circuits: slope {slope:.2f}, R^2 {r2:.2f}.",
            f"- Within cells (seed-to-seed differences only): slope {slope_c:.2f}, R^2 {r2_c:.2f}.", ""]

    # 2. Does a simple gate count rank seeds within a cell?
    rows = []
    for name, key in (("two-qubit gate count", "n2q"), ("two-qubit depth", "depth2q"), ("cost score F", "fidelity_score")):
        rho = np.array([spearmanr([r[key] for r in cells[k]], [r["r"] for r in cells[k]]).statistic for k in keys], dtype=float)
        t = bootstrap(lambda i: np.nanmean(rho[i]), len(rho))
        rows.append(f"- {name}: mean within-cell Spearman correlation with the measured ratio {t[0]:.3f} (95% CI {t[1]:.3f} to {t[2]:.3f})")
    out += ["## 2. Within-cell rank correlation with the measured ratio", ""] + rows + [""]

    # 3. Is the seed effect carried by a few cells?
    S2 = np.array([np.var([r["r"] for r in cells[k]], ddof=1) for k in keys])
    E2 = np.array([np.mean([r["se"] ** 2 for r in cells[k]]) for k in keys])
    order = np.argsort(S2)[::-1]
    loo = [S2[np.arange(len(S2)) != i].mean() / E2[np.arange(len(E2)) != i].mean() for i in range(len(S2))]
    out += ["## 3. Concentration of the seed effect",
            f"- Largest cell: n={keys[order[0]][0]}, graph {keys[order[0]][1]}, p={keys[order[0]][2]}, seed s.d. {np.sqrt(S2[order[0]]):.4f}, "
            f"{S2[order[0]] / S2.sum():.0%} of the total seed variance; top 3 cells carry {S2[order[:3]].sum() / S2.sum():.0%}.",
            f"- Pooled R (shot-noise-only denominator) after dropping any single cell: {min(loo):.1f} to {max(loo):.1f} (all cells: {S2.mean() / E2.mean():.1f}).",
            f"- Cells whose seed variance exceeds twice their shot-noise variance: {int((S2 > 2 * E2).sum())} of {len(S2)}.", ""]
    text = "\n".join(out)
    Path(OUT / "exploratory.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
