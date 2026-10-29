"""Exact statevector QAOA for MaxCut.

Convention: C(x) = number of cut edges, U_C(gamma) = exp(-i gamma C), U_B(beta) = exp(-i beta sum_q X_q),
|psi(gamma, beta)> = prod_l U_B(beta_l) U_C(gamma_l) |+>^n. Parameter vector: [gamma_1..gamma_p, beta_1..beta_p].
QAOA maximises <C>. Bit q of a basis-state index is qubit q (Qiskit's little-endian order).
"""
from __future__ import annotations

import numpy as np

from .graphs import Edges, cut_values


class QAOA:
    def __init__(self, n: int, edges: Edges):
        self.n, self.edges = n, edges
        self.dim = 2**n
        self.cut = cut_values(n, edges)
        self.cmax = float(self.cut.max())
        self.optimal = self.cut == self.cmax

    def _mixer(self, psi: np.ndarray, beta: float) -> np.ndarray:
        c, s = np.cos(beta), -1j * np.sin(beta)
        for q in range(self.n):
            v = psi.reshape(-1, 2, 2**q)
            out = np.empty_like(v)
            out[:, 0, :] = c * v[:, 0, :] + s * v[:, 1, :]
            out[:, 1, :] = c * v[:, 1, :] + s * v[:, 0, :]
            psi = out.reshape(-1)
        return psi

    def state(self, params) -> np.ndarray:
        params = np.asarray(params, dtype=float)
        p = len(params) // 2
        gammas, betas = params[:p], params[p:]
        psi = np.full(self.dim, 1.0 / np.sqrt(self.dim), dtype=complex)
        for g, b in zip(gammas, betas):
            psi = self._mixer(psi * np.exp(-1j * g * self.cut), b)
        return psi

    def probabilities(self, params) -> np.ndarray:
        return np.abs(self.state(params)) ** 2

    def expectation(self, params) -> float:
        return float(self.probabilities(params) @ self.cut)

    def sample_cuts(self, params, shots: int, rng: np.random.Generator) -> np.ndarray:
        """Cut values of `shots` measured bitstrings (finite-shot sampling from the exact distribution)."""
        cdf = np.cumsum(self.probabilities(params))
        idx = np.minimum(np.searchsorted(cdf, rng.random(shots) * cdf[-1]), self.dim - 1)
        return self.cut[idx]

    def p_optimal(self, params) -> float:
        """Probability that one shot returns a maximum cut."""
        return float(self.probabilities(params)[self.optimal].sum())
