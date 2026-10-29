import networkx as nx
import numpy as np
import pytest
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

from qaoa_study.circuit import qaoa_circuit
from qaoa_study.graphs import cubic_instances
from qaoa_study.qaoa import QAOA


def _edges(n, seed):
    g = nx.random_regular_graph(3, n, seed=seed)
    return sorted((min(u, v), max(u, v)) for u, v in g.edges())


@pytest.mark.parametrize("n", [4, 6, 8])
@pytest.mark.parametrize("p", [1, 2, 3])
def test_matches_qiskit_statevector(n, p):
    """Independent implementation: the numpy simulator and Qiskit give the same state (up to global phase)."""
    edges = _edges(n, seed=n + p)
    x = np.random.default_rng(10 * n + p).uniform(-3, 3, 2 * p)
    model = QAOA(n, edges)
    reference = Statevector(qaoa_circuit(n, edges, x)).data
    assert abs(np.vdot(reference, model.state(x))) == pytest.approx(1.0, abs=1e-10)
    assert np.allclose(np.abs(reference) ** 2, model.probabilities(x), atol=1e-10)


def test_zero_parameters_give_the_uniform_cut():
    model = QAOA(6, _edges(6, 1))
    assert model.expectation([0.0, 0.0]) == pytest.approx(len(model.edges) / 2)


def test_state_is_normalised_and_expectation_bounded():
    model = QAOA(8, _edges(8, 3))
    x = np.random.default_rng(0).uniform(-3, 3, 6)
    assert np.linalg.norm(model.state(x)) == pytest.approx(1.0)
    assert 0 <= model.expectation(x) <= model.cmax


def test_periodicity_and_time_reversal_symmetry():
    model = QAOA(6, _edges(6, 2))
    g, b = 0.7, 0.3
    base = model.expectation([g, b])
    assert model.expectation([g + 2 * np.pi, b + np.pi]) == pytest.approx(base)
    assert model.expectation([-g, -b]) == pytest.approx(base)


def test_single_edge_closed_form():
    """p = 1 on one edge: <C> = 1/2 + sin(4 beta) sin(gamma) / 2."""
    model = QAOA(2, [(0, 1)])
    for g, b in np.random.default_rng(0).uniform(0, 3, (20, 2)):
        assert model.expectation([g, b]) == pytest.approx(0.5 + 0.5 * np.sin(4 * b) * np.sin(g), abs=1e-12)


@pytest.mark.parametrize("n", [6, 8])
def test_ring_p1_reaches_three_quarters_of_the_edges(n):
    """Known p = 1 result for the ring of disagrees (Farhi, Goldstone, Gutmann 2014, arXiv:1411.4028)."""
    model = QAOA(n, [(i, (i + 1) % n) for i in range(n)])
    grid_g, grid_b = np.linspace(0, 2 * np.pi, 121), np.linspace(0, np.pi, 121)
    best = max(model.expectation([g, b]) for g in grid_g for b in grid_b)
    assert best / n == pytest.approx(0.75, abs=1e-3)


def test_sampling_matches_the_distribution():
    model = QAOA(6, _edges(6, 4))
    x = [0.6, 0.35]
    cuts = model.sample_cuts(x, 200_000, np.random.default_rng(0))
    assert cuts.mean() == pytest.approx(model.expectation(x), abs=0.02)


def test_p_optimal_is_a_probability_and_uniform_at_zero():
    model = QAOA(6, _edges(6, 5))
    assert model.p_optimal([0.0, 0.0]) == pytest.approx(model.optimal.sum() / model.dim)


def test_instance_enumeration_is_complete_and_valid():
    """Random sampling must recover every connected cubic graph on 8 and 10 vertices (5 and 19, OEIS A004109)."""
    for n, count in [(8, 5), (10, 19)]:
        graphs = cubic_instances(n, max_instances=100)
        assert len(graphs) == count
        for edges in graphs:
            g = nx.Graph(edges)
            assert nx.is_connected(g) and all(d == 3 for _, d in g.degree())


def test_p1_optimum_is_one_constant_on_triangle_free_cubic_graphs():
    """p = 1 depends only on local structure, so every triangle-free 3-regular graph has <C>/|E| = 0.6924 at its optimum
    (Farhi, Goldstone, Gutmann 2014). Checks the simulator and the optimiser against theory on real instances."""
    checked = 0
    for edges in cubic_instances(10, max_instances=19):
        if sum(nx.triangles(nx.Graph(edges)).values()):
            continue
        model = QAOA(10, edges)
        grid = [(a, b) for a in np.linspace(0, np.pi, 41) for b in np.linspace(0, np.pi / 2, 21)]
        x0 = max(grid, key=model.expectation)
        res = minimize(lambda x: -model.expectation(x), x0, method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-12})
        assert -res.fun / len(edges) == pytest.approx(0.69245, abs=2e-5)
        checked += 1
    assert checked > 0
