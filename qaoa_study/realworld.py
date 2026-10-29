"""Small real-world networks as MaxCut instances (docs/PREREGISTRATION_REALWORLD.md).

The networks ship inside networkx (no download): Zachary's karate club (1977), Padgett's Florentine families,
Knuth's Les Miserables co-appearances (Stanford GraphBase, 1993) and the Davis-Gardner-Gardner Southern women (1941).
Edge weights are dropped: the instances are unweighted MaxCut.
"""
from __future__ import annotations

import networkx as nx

from .graphs import Edges

K = 16  # qubits per instance: exact simulation of 2^16 amplitudes is fast


def _largest_component(g: nx.Graph) -> nx.Graph:
    return g.subgraph(max(nx.connected_components(g), key=len)).copy()


def _ranked(g: nx.Graph) -> list:
    return sorted(g.nodes, key=lambda v: (-g.degree(v), str(v)))


def core(g: nx.Graph, k: int = K) -> nx.Graph:
    """Induced subgraph on the k highest-degree nodes (ties by name), largest connected component."""
    return _largest_component(g.subgraph(_ranked(g)[:k]))


def ball(g: nx.Graph, k: int = K) -> nx.Graph:
    """Induced subgraph on the first k nodes of a breadth-first search from the highest-degree node (neighbours in name order)."""
    root = _ranked(g)[0]
    seen, queue = [root], [root]
    while queue and len(seen) < k:
        for u in sorted(g.neighbors(queue.pop(0)), key=str):
            if u not in seen and len(seen) < k:
                seen.append(u)
                queue.append(u)
    return g.subgraph(seen).copy()


def edges_of(g: nx.Graph) -> tuple[int, Edges]:
    order = {v: i for i, v in enumerate(sorted(g.nodes, key=str))}
    return len(order), sorted((min(order[a], order[b]), max(order[a], order[b])) for a, b in g.edges if a != b)


def real_world_instances() -> list[dict]:
    out = []
    florentine = _largest_component(nx.florentine_families_graph())
    out.append(("florentine_families (whole network, largest component)", florentine))
    for name, g in (("karate_club", nx.karate_club_graph()), ("les_miserables", nx.les_miserables_graph()),
                    ("davis_southern_women", nx.davis_southern_women_graph())):
        c, b = core(g), ball(g)
        out.append((f"{name} core-{K}", c))
        if set(b.nodes) != set(c.nodes):
            out.append((f"{name} ball-{K}", b))
    result = []
    for label, g in out:
        n, edges = edges_of(g)
        result.append({"name": label, "n": n, "edges": edges, "bipartite": nx.is_bipartite(g), "connected": nx.is_connected(g)})
    return result
