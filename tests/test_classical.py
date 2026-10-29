import networkx as nx
import numpy as np
import pytest

from qaoa_study.classical import adjacency, cut_of, gw_round, gw_sdp, local_search
from qaoa_study.graphs import cut_values, maxcut


def test_cut_values_match_networkx():
    g = nx.random_regular_graph(3, 6, seed=0)
    edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
    c = cut_values(6, edges)
    for x in (0b000000, 0b010101, 0b001011, 0b111000):
        side = {v: (x >> v) & 1 for v in range(6)}
        a = {v for v in side if side[v]}
        assert c[x] == nx.cut_size(g, a)


def test_maxcut_of_triangle_and_even_cycle():
    assert maxcut(3, [(0, 1), (1, 2), (0, 2)]) == (2.0, 6)
    assert maxcut(4, [(0, 1), (1, 2), (2, 3), (0, 3)]) == (4.0, 2)


def test_sdp_value_of_the_triangle_is_nine_quarters():
    """Three unit vectors at 120 degrees: each edge contributes (1 - cos 120)/2 = 3/4."""
    value, _ = gw_sdp(3, [(0, 1), (1, 2), (0, 2)])
    assert value == pytest.approx(2.25, abs=1e-6)


def test_sdp_of_a_bipartite_graph_equals_the_edge_count():
    value, _ = gw_sdp(6, [(i, (i + 1) % 6) for i in range(6)])
    assert value == pytest.approx(6.0, abs=1e-6)


def test_sdp_upper_bounds_the_exact_maxcut_on_cubic_graphs():
    for seed in range(5):
        g = nx.random_regular_graph(3, 10, seed=seed)
        edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
        value, V = gw_sdp(10, edges)
        cmax, _ = maxcut(10, edges)
        assert cmax - 1e-6 <= value <= len(edges)
        assert np.allclose(np.linalg.norm(V, axis=1), 1.0)


def test_rounding_never_exceeds_the_maximum_cut():
    g = nx.random_regular_graph(3, 10, seed=1)
    edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
    _, V = gw_sdp(10, edges)
    cuts = gw_round(V, edges, 500, np.random.default_rng(0))
    assert cuts.max() <= maxcut(10, edges)[0]
    # Goemans-Williamson guarantee on the expected rounded cut, relative to the SDP value (0.878...)
    value, _ = gw_sdp(10, edges)
    assert cuts.mean() >= 0.87 * value


def test_local_search_ends_at_a_one_flip_local_optimum():
    g = nx.random_regular_graph(3, 12, seed=2)
    edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
    adj = adjacency(12, edges)
    rng = np.random.default_rng(0)
    for _ in range(20):
        seed_rng = np.random.default_rng(rng.integers(1000))
        reached = local_search(adj, edges, seed_rng)
        assert reached <= maxcut(12, edges)[0]
        # at a 1-flip optimum of a cubic graph every vertex has at most one uncut edge, so >= 2/3 of the edges are cut
        assert reached >= 2 * len(edges) / 3
