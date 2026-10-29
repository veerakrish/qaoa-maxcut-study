"""CV-sized versions of the three main QAOA figures, regenerated from the committed result files (no new analysis).

    python -m qaoa_study.cv_figures        # writes figures/cv_simulation.png, cv_hardware.png, cv_realworld.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .analysis import boot
from .analysis_hardware import load_runs

DEPTHS = (1, 2, 3)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
                     "legend.fontsize": 6.8, "figure.dpi": 200, "savefig.dpi": 200})


def _best(runs, mode, p, fn):
    return fn([r["ratio"] for r in runs if r["mode"] == mode and r["p"] == p])


def simulation(out: Path) -> None:
    ideal_best, ideal_mean, shots_mean, base = {p: [] for p in DEPTHS}, {p: [] for p in DEPTHS}, {p: [] for p in DEPTHS}, []
    for f in sorted(Path("results/raw").glob("*.json")):
        d = json.loads(f.read_text())
        for p in DEPTHS:
            ideal_best[p].append(_best(d["runs"], "ideal", p, max))
            ideal_mean[p].append(_best(d["runs"], "ideal", p, np.mean))
            shots_mean[p].append(_best(d["runs"], "shots", p, np.mean))
        base.append(d["baselines"])
    fig, ax = plt.subplots(figsize=(3.55, 3.35))
    fig.subplots_adjust(left=0.17, right=0.97, top=0.97, bottom=0.36)
    for label, data, style in (("QAOA, best of 5 restarts", ideal_best, "o-"), ("QAOA, mean of 5", ideal_mean, "s--"), ("QAOA, 1024-shot objective", shots_mean, "^:")):
        m = np.array([boot(data[p]) for p in DEPTHS])
        ax.plot(DEPTHS, m[:, 0], style, ms=3.5, lw=1.1, label=label)
        ax.fill_between(DEPTHS, m[:, 1], m[:, 2], alpha=0.18)
    for label, key, ls in (("Goemans-Williamson", "gw_single_ratio", "-."), ("local search", "ls_single_ratio", "-"), ("random cut", "random_ratio", ":")):
        ax.axhline(np.mean([b[key] for b in base]), color="gray", ls=ls, lw=0.9, label=label + ", 1 run" if key != "random_ratio" else label)
    ax.set(xlabel="QAOA depth p", ylabel="approximation ratio", xticks=DEPTHS, ylim=(0.55, 1.0))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False, fontsize=6.0, columnspacing=0.8, handlelength=1.6)
    fig.savefig(out / "cv_simulation.png")
    plt.close(fig)


def hardware(out: Path) -> None:
    runs = [r for r in load_runs() if not r["repeat"]]
    cells = {}
    for r in runs:
        cells.setdefault(tuple(r["key"][:3]), []).append(r)
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55), sharey=True)
    for ax, p in zip(axes, (1, 2)):
        ks = sorted(k for k in cells if k[2] == p)
        for x, k in enumerate(ks):
            rs = cells[k]
            ax.errorbar([x] * len(rs), [r["r"] for r in rs], yerr=[r["se"] for r in rs], fmt="o", ms=3, lw=0.8, color="tab:blue", alpha=0.85)
            ax.plot(x, rs[0]["ideal_ratio"], "kx", ms=5)
        ax.axvline(4.5, color="gray", lw=0.6, ls=":")
        ax.set(title=f"p = {p}", xlabel="graph (n = 8: 0-4, n = 10: 5-9)", xticks=range(len(ks)))
    axes[0].set_ylabel("approximation ratio")
    axes[1].plot([], [], "kx", label="noiseless")
    axes[1].plot([], [], "o", color="tab:blue", label="hardware, 5 compiler seeds")
    axes[1].legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig(out / "cv_hardware.png")
    plt.close(fig)


def realworld(out: Path) -> None:
    cubic = {p: [] for p in DEPTHS}
    for f in Path("results/raw").glob("*.json"):
        runs = json.loads(f.read_text())["runs"]
        for p in DEPTHS:
            cubic[p].append(_best(runs, "ideal", p, max))
    names = ["Florentine", "Karate core", "Karate ball", "Les Mis core", "Les Mis ball", "Davis core*", "Davis ball*"]
    fig, ax = plt.subplots(figsize=(3.55, 3.35))
    fig.subplots_adjust(left=0.17, right=0.97, top=0.97, bottom=0.36)
    ax.fill_between(DEPTHS, [min(cubic[p]) for p in DEPTHS], [max(cubic[p]) for p in DEPTHS], color="gray", alpha=0.25, label="range, 64 cubic graphs")
    for name, f in zip(names, sorted(Path("results/realworld/raw").glob("*.json"))):
        d = json.loads(f.read_text())
        ax.plot(DEPTHS, [_best(d["runs"], "ideal", p, max) for p in DEPTHS], "o-", ms=3, lw=1.0, label=name)
    ax.set(xlabel="QAOA depth p", ylabel="approximation ratio (best of 5)", xticks=DEPTHS, ylim=(0.48, 1.0))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False, fontsize=6.4)
    fig.savefig(out / "cv_realworld.png")
    plt.close(fig)


def main() -> None:
    out = Path("figures")
    out.mkdir(exist_ok=True)
    simulation(out)
    hardware(out)
    realworld(out)
    print("wrote", ", ".join(sorted(p.name for p in out.glob("cv_*.png"))))


if __name__ == "__main__":
    main()
