"""Classical baselines: random cut, Goemans-Williamson rounding, 1-flip local search."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .graphs import Edges


def gw_sdp(n: int, edges: Edges, seed: int = 0, restarts: int = 4) -> tuple[float, np.ndarray]:
    """Value and unit vectors of the MaxCut SDP relaxation, by Burer-Monteiro low-rank ascent.

    Rank ceil(sqrt(2n)) + 1 is large enough that the low-rank problem has no spurious local optima
    (Barvinok-Pataki). This is a local solver, not a certified SDP solve; the value is checked against the
    exact maximum cut (an upper bound) by the caller.
    """
    ia = np.array([a for a, _ in edges])
    ib = np.array([b for _, b in edges])
    r = int(np.ceil(np.sqrt(2 * n))) + 1
    rng = np.random.default_rng(seed)

    def loss_grad(u):
        U = u.reshape(n, r)
        norms = np.linalg.norm(U, axis=1, keepdims=True)
        V = U / norms
        dots = np.einsum("ij,ij->i", V[ia], V[ib])
        loss = 0.5 * dots.sum() - 0.5 * len(edges)  # minus the SDP objective sum (1 - v_a.v_b)/2
        G = np.zeros_like(V)
        np.add.at(G, ia, 0.5 * V[ib])
        np.add.at(G, ib, 0.5 * V[ia])
        G = (G - np.sum(G * V, axis=1, keepdims=True) * V) / norms
        return loss, G.ravel()

    best = None
    for _ in range(restarts):
        res = minimize(loss_grad, rng.standard_normal(n * r), jac=True, method="L-BFGS-B", options={"maxiter": 2000})
        if best is None or res.fun < best.fun:
            best = res
    U = best.x.reshape(n, r)
    return -float(best.fun), U / np.linalg.norm(U, axis=1, keepdims=True)


def gw_round(V: np.ndarray, edges: Edges, shots: int, rng: np.random.Generator) -> np.ndarray:
    """Cut values of `shots` independent random-hyperplane roundings."""
    side = (V @ rng.standard_normal((V.shape[1], shots))) > 0
    return sum((side[a] != side[b]).astype(float) for a, b in edges)


def adjacency(n: int, edges: Edges) -> list[list[int]]:
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def cut_of(x, edges: Edges) -> float:
    return float(sum(x[a] != x[b] for a, b in edges))


def local_search(adj: list[list[int]], edges: Edges, rng: np.random.Generator) -> float:
    """First-improvement 1-flip local search from a uniformly random cut; returns the cut value reached."""
    x = rng.integers(0, 2, len(adj))
    improved = True
    while improved:
        improved = False
        for v in rng.permutation(len(adj)):
            same = sum(x[u] == x[v] for u in adj[v])
            if same > len(adj[v]) - same:
                x[v] ^= 1
                improved = True
    return cut_of(x, edges)
