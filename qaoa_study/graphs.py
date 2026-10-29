"""Problem instances (unique connected 3-regular graphs) and exact MaxCut by enumeration."""
from __future__ import annotations

import networkx as nx
import numpy as np

# Number of connected cubic graphs on n vertices (OEIS A004109); caps the instance count at small n.
CONNECTED_CUBIC_COUNT = {6: 2, 8: 5, 10: 19, 12: 85, 14: 509}

Edges = list[tuple[int, int]]


def cubic_instances(n: int, max_instances: int = 20) -> list[Edges]:
    """Up to `max_instances` pairwise non-isomorphic connected 3-regular graphs on n vertices.

    Deterministic in n. For n = 8 and 10 this returns every such graph (5 and 19), because
    random sampling of so few graphs would otherwise repeat isomorphic instances.
    """
    target = min(max_instances, CONNECTED_CUBIC_COUNT[n])
    rng = np.random.default_rng(1000 * n)
    found: list[nx.Graph] = []
    for _ in range(200_000):
        if len(found) == target:
            break
        g = nx.random_regular_graph(3, n, seed=int(rng.integers(2**31 - 1)))
        if not nx.is_connected(g) or any(nx.is_isomorphic(g, h) for h in found):
            continue
        found.append(g)
    if len(found) < target:
        raise RuntimeError(f"found only {len(found)} of {target} graphs for n={n}")
    return [sorted((min(u, v), max(u, v)) for u, v in g.edges()) for g in found]


def cut_values(n: int, edges: Edges) -> np.ndarray:
    """Cut value of every bitstring; bit q of the index is the side of vertex q."""
    x = np.arange(2**n)
    c = np.zeros(2**n)
    for a, b in edges:
        c += ((x >> a) & 1) ^ ((x >> b) & 1)
    return c


def maxcut(n: int, edges: Edges) -> tuple[float, int]:
    """(maximum cut, number of bitstrings achieving it). Includes the complement of every optimum."""
    c = cut_values(n, edges)
    cmax = float(c.max())
    return cmax, int(np.sum(c == cmax))
