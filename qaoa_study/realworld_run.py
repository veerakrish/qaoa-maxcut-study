"""Run the pre-registered real-world-network check and apply its decision rules (docs/PREREGISTRATION_REALWORLD.md).

    python -m qaoa_study.realworld_run          # run (one JSON per instance, resumable) then report
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .analysis import md_table
from .experiment import Config, run_instance
from .realworld import real_world_instances

OUT = Path("results/realworld")
CFG = Config(sizes=(15, 16), depths=(1, 2, 3), restarts=5, modes=("ideal",))
DEPTHS, TOL = (1, 2, 3), 0.002


def run() -> None:
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    (OUT / "config.json").write_text(json.dumps(asdict(CFG), indent=2))
    insts = real_world_instances()
    todo = [i for i in range(len(insts)) if not (OUT / "raw" / f"{i:02d}.json").exists()]
    tasks = [(insts[i]["n"], i, insts[i]["edges"], asdict(CFG)) for i in todo]
    with ProcessPoolExecutor() as pool:
        for i, res in zip(todo, pool.map(run_instance, tasks)):
            res["name"], res["bipartite"] = insts[i]["name"], insts[i]["bipartite"]
            (OUT / "raw" / f"{i:02d}.json").write_text(json.dumps(res))
            print(f"done {insts[i]['name']} ({res['seconds']} s)", flush=True)


def _cubic_ranges() -> dict:
    best = {p: [] for p in DEPTHS}
    for f in Path("results/raw").glob("*.json"):
        runs = json.loads(f.read_text())["runs"]
        for p in DEPTHS:
            best[p].append(max(r["ratio"] for r in runs if r["mode"] == "ideal" and r["p"] == p))
    return {p: (min(v), max(v)) for p, v in best.items()}


def report() -> str:
    data = [json.loads(f.read_text()) for f in sorted((OUT / "raw").glob("*.json"))]
    cubic = _cubic_ranges()
    rows, rb_all, gates = [], [], []
    rw1 = rw2 = 0
    for d in data:
        runs = [r for r in d["runs"] if r["mode"] == "ideal"]
        rb = {p: max(r["ratio"] for r in runs if r["p"] == p) for p in DEPTHS}
        rm = {p: sum(r["ratio"] for r in runs if r["p"] == p) / sum(1 for r in runs if r["p"] == p) for p in DEPTHS}
        b = d["baselines"]
        best3 = max((r for r in runs if r["p"] == 3), key=lambda r: r["ratio"])
        ok1 = rb[2] >= rb[1] - TOL and rb[3] >= rb[2] - TOL
        below = rb[3] < b["gw_single_ratio"] and rb[3] < b["ls_single_ratio"]
        rw1, rw2 = rw1 + ok1, rw2 + below
        gates.append(max(r["ratio"] for r in runs) <= 1 + 1e-9 and b["sdp_value"] >= b["cmax"] - 1e-6)
        pos = lambda p: "below" if rb[p] < cubic[p][0] else ("above" if rb[p] > cubic[p][1] else "inside")
        rb_all.append((d, rb, b))
        rows.append({"graph": d["name"], "n": d["n"], "edges": len(d["edges"]), "bipartite": "yes" if d["bipartite"] else "no",
                     "r_best p=1": f"{rb[1]:.3f}", "p=2": f"{rb[2]:.3f}", "p=3": f"{rb[3]:.3f}", "r_mean p=3": f"{rm[3]:.3f}",
                     "GW single": f"{b['gw_single_ratio']:.3f}", "local search single": f"{b['ls_single_ratio']:.3f}", "random cut": f"{b['random_ratio']:.3f}",
                     "RW1 non-decreasing": "yes" if ok1 else "NO", "RW2 below both": "yes" if below else "NO",
                     "RW3 vs cubic (p=1/2/3)": "/".join(pos(p) for p in DEPTHS),
                     "RW4 P(opt) p=3": f"{best3['p_optimal']:.3f} ({best3['p_optimal'] / b['uniform_p_optimal']:.0f}x uniform)",
                     "RW4 p=1 minus random": f"{rb[1] - b['random_ratio']:+.3f}"})
    n = len(data)
    text = "\n".join([
        "# Real-world networks: results", "",
        f"{n} instances, QAOA p = 1-3, five restarts each, exact simulation. Per-graph results only (too few graphs for intervals). Decision rules: `docs/PREREGISTRATION_REALWORLD.md`.", "",
        "## Validation gates", "", f"- {'PASS' if all(gates) else 'FAIL'}: SDP value >= exact maximum cut and no ratio above 1 on every graph", "",
        "## Per graph", "", md_table(rows), "",
        "## Verdicts", "",
        f"- **RW1** (non-decreasing in p within {TOL}): holds on {rw1} of {n} graphs.",
        f"- **RW2** (p = 3 below both single-run classical baselines): holds on {rw2} of {n} graphs.",
        "- **RW3**: range of `r_best` over the 64 cubic graphs: " + "; ".join(f"p={p}: {lo:.3f} to {hi:.3f}" for p, (lo, hi) in cubic.items()) + ".", ""])
    (OUT / "summary.md").write_text(text, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.fill_between(DEPTHS, [cubic[p][0] for p in DEPTHS], [cubic[p][1] for p in DEPTHS], color="gray", alpha=0.25, label="range over 64 cubic graphs")
    for d, rb, b in rb_all:
        line, = ax.plot(DEPTHS, [rb[p] for p in DEPTHS], "o-", ms=4, lw=1.2, label=d["name"].replace(" (whole network, largest component)", ""))
        ax.plot([3.15], [b["gw_single_ratio"]], "x", color=line.get_color())
        ax.plot([3.3], [b["ls_single_ratio"]], "+", color=line.get_color())
    ax.set(xlabel="QAOA depth p   (x: Goemans-Williamson, +: local search, single run)", ylabel="approximation ratio <C> / C_max", xticks=DEPTHS, xlim=(0.8, 3.5))
    ax.legend(fontsize=6.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "ratio_vs_p.png", dpi=160)
    plt.close(fig)
    return text


if __name__ == "__main__":
    run()
    print(report())
