"""Apply the decision rules HW1-HW5 of docs/PREREGISTRATION_HARDWARE.md to results/hardware/hardware_results.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from .analysis import fmt, md_table
from .graphs import cut_values
from .hardware import OUT, instances


def load_runs(out: Path = OUT, raw_dir: str = "results/raw") -> list[dict]:
    plan = json.loads((out / "plan.json").read_text())
    res = json.loads((out / "hardware_results.json").read_text())
    assert res["plan_hash"] == plan["hash"], "results do not belong to this plan"
    counts = {r["position"]: r["counts"] for r in res["results"]}
    edges = {(i["n"], i["graph"]): i["edges"] for i in instances(raw_dir)}
    cuts, runs = {}, []
    for c in plan["circuits"]:
        n, g, p, seed = c["key"]
        cv = cuts.setdefault((n, g), cut_values(n, edges[(n, g)]))
        cnt = counts[c["position"]]
        shots = sum(cnt.values())
        vals = np.repeat([cv[int(b, 2)] for b in cnt], list(cnt.values()))
        runs.append({**c, "r": float(vals.mean() / c["cmax"]), "se": float(vals.std(ddof=1) / np.sqrt(shots) / c["cmax"]),
                     "shots": shots, "repeat": bool(c.get("repeat", False))})
    return runs


def bootstrap(stat, n: int, B: int = 10_000, seed: int = 0) -> tuple[float, float, float]:
    """Estimate and 95% percentile interval of stat(index array), resampling cells (or graphs) with replacement."""
    rng = np.random.default_rng(seed)
    draws = np.array([stat(rng.integers(0, n, n)) for _ in range(B)])
    return float(stat(np.arange(n))), float(np.nanpercentile(draws, 2.5)), float(np.nanpercentile(draws, 97.5))


def analyse(runs: list[dict], out: Path = OUT) -> str:
    cells: dict = {}
    for r in runs:
        if not r["repeat"]:
            cells.setdefault(tuple(r["key"][:3]), []).append(r)
    for k in cells:
        cells[k].sort(key=lambda r: r["key"][3])
        assert len(cells[k]) == 5, f"cell {k} has {len(cells[k])} seeds"
    keys = sorted(cells)
    refs = [r for r in runs if r["repeat"]]
    drift = max(float(np.var([r["r"] for r in refs], ddof=1) - np.mean([r["se"] ** 2 for r in refs])), 0.0)

    S2 = np.array([np.var([r["r"] for r in cells[k]], ddof=1) for k in keys])
    E2 = np.array([np.mean([r["se"] ** 2 for r in cells[k]]) for k in keys]) + drift
    P = np.array([k[2] for k in keys])
    out_md = ["# Hardware results (pre-registered analysis)", "",
              f"{len(runs)} circuits ({len(keys)} cells x 5 seeds, plus {len(refs)} reference repeats). Intervals are 95% bootstrap over cells (graphs for HW2).", ""]

    # HW1
    rows, detected = [], False
    for label, sel in (("p = 1", P == 1), ("p = 2", P == 2), ("pooled", P > 0)):
        s, e = S2[sel], E2[sel]
        t = bootstrap(lambda i: s[i].mean() / e[i].mean(), len(s))
        rows.append({"cells": label, "mean seed variance": f"{s.mean():.2e}", "mean expected (shot noise + drift)": f"{e.mean():.2e}",
                     "R [95% CI]": fmt(t, 2), "seed effect detected (lower bound > 1)": "yes" if t[1] > 1 else "no"})
        detected = t[1] > 1 if label == "pooled" else detected
    out_md += ["## HW1: is there a seed-level effect beyond shot noise and drift?", "",
               f"**Pooled verdict: {'DETECTED' if detected else 'NOT DETECTED'}.** Drift variance from the reference repeats: {drift:.2e} "
               f"(reference repeats: mean r = {np.mean([r['r'] for r in refs]):.4f}, s.d. = {np.std([r['r'] for r in refs], ddof=1):.4f}, mean shot-noise s.e. = {np.mean([r['se'] for r in refs]):.4f}).", "",
               md_table(rows), ""]

    # HW2
    excess_sd = float(np.sqrt(max(S2.mean() - E2.mean(), 0.0)))
    graphs = sorted({(k[0], k[1]) for k in keys})
    delta = np.array([np.mean([r["r"] for r in cells[(n, g, 2)]]) - np.mean([r["r"] for r in cells[(n, g, 1)]]) for n, g in graphs])
    td = bootstrap(lambda i: delta[i].mean(), len(delta))
    comparable = excess_sd >= 0.5 * abs(td[0])
    out_md += ["## HW2: seed spread against the depth gain (descriptive)", "",
               f"Excess seed s.d. = {excess_sd:.4f}. Measured ratio at p = 2 minus p = 1, per graph: mean {fmt(td, 4)} (10 graphs). "
               f"**Seed spread is {'COMPARABLE to' if comparable else 'smaller than half of'} the depth gain** (rule: seed s.d. >= 0.5 x |mean difference|). "
               f"p = 2 {'beats' if td[1] > 0 else 'does not clearly beat'} p = 1 on hardware.", ""]

    # HW3
    rho = np.array([spearmanr([r["fidelity_score"] for r in cells[k]], [r["r"] for r in cells[k]]).statistic for k in keys], dtype=float)
    tr = bootstrap(lambda i: np.nanmean(rho[i]), len(rho))
    out_md += ["## HW3: does the cost score predict the measured ratio across seeds?", "",
               f"Mean within-cell Spearman correlation {fmt(tr, 3)} ({int(np.isnan(rho).sum())} cells with constant scores dropped). "
               f"**{'PREDICTIVE' if tr[1] > 0 else 'NOT shown to be predictive'}** (lower bound {'>' if tr[1] > 0 else 'not >'} 0).", ""]

    # HW4
    a = np.array([min(cells[k], key=lambda r: (r["n2q"], r["key"][3]))["r"] for k in keys])
    b = np.array([max(cells[k], key=lambda r: r["fidelity_score"])["r"] for k in keys])
    c = np.array([np.mean([r["r"] for r in cells[k]]) for k in keys])
    rows = []
    for name, x in (("cost score vs random seed (b - c)", b - c), ("fewest two-qubit gates vs random seed (a - c)", a - c),
                    ("cost score vs fewest two-qubit gates (b - a)", b - a)):
        t = bootstrap(lambda i: x[i].mean(), len(x))
        rows.append({"comparison": name, "mean difference in measured ratio [95% CI]": fmt(t, 4), "interval above 0": "yes" if t[1] > 0 else "no"})
    helps = bootstrap(lambda i: (b - c)[i].mean(), len(c))[1] > 0
    out_md += ["## HW4: selection rules", "", f"**The cost score {'HELPS' if helps else 'is NOT shown to help'} over a random seed** (needs (b - c) above 0).", "", md_table(rows), ""]

    # HW5
    rows = []
    for n in (8, 10):
        for p in (1, 2):
            sel = [r for r in runs if not r["repeat"] and r["key"][0] == n and r["key"][2] == p]
            rows.append({"n": n, "p": p, "mean measured ratio": f"{np.mean([r['r'] for r in sel]):.3f}", "mean ideal ratio": f"{np.mean([r['ideal_ratio'] for r in sel]):.3f}",
                         "measured / ideal": f"{np.mean([r['r'] / r['ideal_ratio'] for r in sel]):.3f}", "mean cost score F": f"{np.mean([r['fidelity_score'] for r in sel]):.3f}"})
    out_md += ["## HW5: hardware against ideal (descriptive)", "", md_table(rows), "",
               "For reference, a uniformly random cut has ratio about 0.58 on these graphs.", ""]

    text = "\n".join(out_md)
    (out / "summary.md").write_text(text, encoding="utf-8")
    _figures(cells, keys, out)
    return text


def _figures(cells: dict, keys: list, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, p in zip(axes, (1, 2)):
        ks = [k for k in keys if k[2] == p]
        for x, k in enumerate(ks):
            rs = cells[k]
            ax.errorbar([x] * 5, [r["r"] for r in rs], yerr=[r["se"] for r in rs], fmt="o", ms=4, color="tab:blue", alpha=0.8)
            ax.plot(x, rs[0]["ideal_ratio"], "kx")
        ax.set(title=f"p = {p}", xlabel="graph (n = 8 then n = 10)", xticks=range(len(ks)))
    axes[0].set_ylabel("measured approximation ratio (5 seeds per graph)")
    axes[1].plot([], [], "kx", label="ideal (noiseless)")
    axes[1].plot([], [], "o", color="tab:blue", label="hardware, +/- shot-noise s.e.")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "hardware_seed_spread.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.8, 3.8))
    for p, col in ((1, "tab:blue"), (2, "tab:orange")):
        dx, dy = [], []
        for k in keys:
            if k[2] == p:
                f = np.array([r["fidelity_score"] for r in cells[k]])
                m = np.array([r["r"] for r in cells[k]])
                dx += list(f - f.mean())
                dy += list(m - m.mean())
        ax.scatter(dx, dy, s=14, color=col, label=f"p = {p}", alpha=0.7)
    ax.axhline(0, color="gray", lw=0.6)
    ax.axvline(0, color="gray", lw=0.6)
    ax.set(xlabel="cost score F minus cell mean", ylabel="measured ratio minus cell mean")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "hardware_cost_score.png", dpi=160)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=str(OUT))
    a = ap.parse_args(argv)
    print(analyse(load_runs(Path(a.dir)), Path(a.dir)))


if __name__ == "__main__":
    main()
