"""The same QAOA as a Qiskit circuit: used to cross-check the numpy simulator, and the entry point for later hardware work."""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit

from .graphs import Edges


def qaoa_circuit(n: int, edges: Edges, params, measure: bool = False) -> QuantumCircuit:
    """exp(-i gamma C) with C = sum_edges (1 - Z_a Z_b)/2 equals, up to a global phase, RZZ(-gamma) on every edge."""
    params = np.asarray(params, dtype=float)
    p = len(params) // 2
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for gamma, beta in zip(params[:p], params[p:]):
        for a, b in edges:
            qc.rzz(-gamma, a, b)
        for q in range(n):
            qc.rx(2 * beta, q)
    if measure:
        qc.measure_all()
    return qc
