"""Run the pre-registered experiment (docs/PREREGISTRATION.md). One JSON file per instance, resumable."""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from .classical import adjacency, gw_round, gw_sdp, local_search
from .graphs import Edges, cubic_instances
from .qaoa import QAOA


@dataclass(frozen=True)
class Config:
    sizes: tuple = (8, 10, 12, 14)
    max_instances: int = 20
    depths: tuple = (1, 2, 3)
    restarts: int = 5
    shots_per_eval: int = 1024      # shot-limited optimisation: shots per objective evaluation
    final_shots: int = 1024         # shots used for the best-of-S metric at the final parameters
    maxiter: int = 300
    baseline_samples: int = 1024    # GW roundings / random cuts per instance
    local_search_runs: int = 200
    modes: tuple = ("ideal", "shots")


MODES = {"ideal": 0, "shots": 1}


def _rng(*key: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence(list(key)))


def optimise(model: QAOA, p: int, init_rng, shot_rng, shots, maxiter: int):
    """COBYLA from a random start gamma ~ U(0, pi), beta ~ U(0, pi/2); maximises <C> (exact or from `shots` samples).

    Both arms use COBYLA's own stopping rule with a cap of `maxiter` evaluations. On a shot-limited objective the
    trust region collapses early (observed: 50-120 evaluations, whatever the tolerance), so the two arms do not
    spend equal budgets; `nfev` and `shots_used` are recorded and the comparison is reported as such.
    """
    x0 = np.concatenate([init_rng.uniform(0, np.pi, p), init_rng.uniform(0, np.pi / 2, p)])
    if shots is None:
        def objective(x):
            return -model.expectation(x)
    else:
        def objective(x):
            return -float(model.sample_cuts(x, shots, shot_rng).mean())
    res = minimize(objective, x0, method="COBYLA", tol=1e-4, options={"rhobeg": 0.3, "maxiter": maxiter})
    return res.x, int(res.nfev)


def baselines(n: int, idx: int, model: QAOA, cfg: Config) -> dict:
    edges, cmax = model.edges, model.cmax
    rng = _rng(n, idx, 7)
    sdp, V = gw_sdp(n, edges, seed=int(rng.integers(2**31)))
    if sdp < cmax - 1e-6:
        raise RuntimeError(f"SDP value {sdp} below exact maximum cut {cmax}: low-rank solver stalled (n={n}, idx={idx})")
    rounded = gw_round(V, edges, cfg.baseline_samples, rng)
    adj = adjacency(n, edges)
    ls = np.array([local_search(adj, edges, rng) for _ in range(cfg.local_search_runs)])
    draws = model.cut[rng.integers(0, model.dim, size=(200, cfg.final_shots))]
    return {
        "cmax": cmax,
        "n_optimal_states": int(model.optimal.sum()),
        "random_ratio": len(edges) / 2 / cmax,
        "random_best_of_S_ratio": float(draws.max(axis=1).mean() / cmax),
        "uniform_p_optimal": float(model.optimal.mean()),
        "sdp_value": sdp,
        "gw_single_ratio": float(rounded.mean() / cmax),
        "gw_best_of_S_ratio": float(rounded.max() / cmax),
        "ls_single_ratio": float(ls.mean() / cmax),
        "ls_best_of_10_ratio": float(ls[: 10 * (len(ls) // 10)].reshape(-1, 10).max(axis=1).mean() / cmax),
    }


def run_instance(task: tuple) -> dict:
    n, idx, edges, cfg_dict = task
    cfg = Config(**{k: tuple(v) if isinstance(v, list) else v for k, v in cfg_dict.items()})
    t0 = time.time()
    model = QAOA(n, edges)
    runs = []
    for p in cfg.depths:
        for restart in range(cfg.restarts):
            for mode, code in MODES.items():
                if mode not in cfg.modes:
                    continue
                init_rng = _rng(n, idx, p, restart, code, 1)
                shot_rng = _rng(n, idx, p, restart, code, 2)
                x, nfev = optimise(model, p, init_rng, shot_rng, cfg.shots_per_eval if mode == "shots" else None, cfg.maxiter)
                expectation = model.expectation(x)
                final = model.sample_cuts(x, cfg.final_shots, _rng(n, idx, p, restart, code, 3))
                runs.append({
                    "p": p, "restart": restart, "mode": mode, "nfev": nfev,
                    "shots_used": nfev * cfg.shots_per_eval if mode == "shots" else 0,
                    "expectation": expectation, "ratio": expectation / model.cmax,
                    "p_optimal": model.p_optimal(x),
                    "best_of_S_ratio": float(final.max() / model.cmax),
                    "params": [float(v) for v in x],
                })
    return {"n": n, "instance": idx, "edges": edges, "baselines": baselines(n, idx, model, cfg),
            "runs": runs, "seconds": round(time.time() - t0, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/raw")
    ap.add_argument("--sizes", type=int, nargs="+")
    ap.add_argument("--max-instances", type=int)
    ap.add_argument("--depths", type=int, nargs="+")
    ap.add_argument("--restarts", type=int)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args(argv)

    overrides = {k: (tuple(v) if isinstance(v, list) else v) for k, v in
                 dict(sizes=args.sizes, max_instances=args.max_instances, depths=args.depths, restarts=args.restarts).items()
                 if v is not None}
    cfg = Config(**overrides)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out.parent / "config.json").write_text(json.dumps(asdict(cfg), indent=2))

    tasks = []
    for n in cfg.sizes:
        for idx, edges in enumerate(cubic_instances(n, cfg.max_instances)):
            if not (out / f"n{n}_i{idx:02d}.json").exists():
                tasks.append((n, idx, edges, asdict(cfg)))
    print(f"{len(tasks)} instance tasks to run ({args.workers} workers)", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, result in enumerate(pool.map(run_instance, tasks), 1):
            (out / f"n{result['n']}_i{result['instance']:02d}.json").write_text(json.dumps(result))
            print(f"[{done}/{len(tasks)}] n={result['n']} instance={result['instance']} {result['seconds']}s "
                  f"(elapsed {time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
