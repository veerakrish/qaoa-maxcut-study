# Literature check

Searched 2026-10-29: about ten web searches plus direct reads of the sources below. **Not a systematic review.** Failing to
find a paper is weak evidence that none exists. Claims are graded by how they were checked.

## Checked at the source (arXiv abstract page or official documentation read in full for the points below)

| Work | What it shows | Why it matters here |
|---|---|---|
| Nation, Treinish. *Suppressing quantum circuit errors due to system variability.* PRX Quantum 4, 010327 (2023); [arXiv:2209.15512](https://arxiv.org/abs/2209.15512) | mapomatic: finds subgraphs isomorphic to a compiled circuit and scores them with calibration-derived cost functions; recovers nearly 40% of lost fidelity on a standard test suite | The calibration-based score in this project's design is this idea. It is not new |
| Weidenfeller et al. *Scaling of the quantum approximate optimization algorithm on superconducting qubit based hardware.* Quantum 6, 870 (2022); [arXiv:2202.03459](https://arxiv.org/abs/2202.03459) | Swap strategies for mapping dense QAOA problems onto linear, grid, heavy-hex and 3D coupling maps; QAOA Qiskit Runtime program with closed-loop optimisation on cloud hardware | Directly about QAOA compilation on IBM-style hardware. Check the authors' affiliations: two co-authors (Woerner, Egger) are, to my knowledge, at IBM Research Zurich, which is the internship's lab (not confirmed on the abstract page) |
| Huo et al. *Revisiting Noise-adaptive Transpilation in Quantum Computing: How Much Impact Does it Have?* [arXiv:2507.01195](https://arxiv.org/abs/2507.01195) (2025) | Five IBM 127-qubit machines, 16 algorithms: noise-aware mapping concentrates work on a few qubits and increases output-error variability; random mapping gives comparable average fidelity; circuits compiled once can be reused across calibration cycles | Closest hardware study of variability caused by mapping. Not QAOA-specific and not seed-level |
| Alam, Ash-Saki, Ghosh. *Analysis of QAOA under Realistic Noise in Superconducting Qubits.* [arXiv:1907.09631](https://arxiv.org/abs/1907.09631) (2019) | Noise limits the useful depth p; deeper QAOA does not always beat shallow | Supports restricting hardware runs to p <= 2 |
| Zou, Treinish, Hartman, Ivrii, Lishman. *LightSABRE.* [arXiv:2409.08368](https://arxiv.org/abs/2409.08368) (2024) | Faster SABRE in Qiskit 1.2.0, 18.9% fewer SWAPs on average than the original SABRE | Qiskit's default router is already heavily optimised |
| Pati, Simmhan. *Per-Phase Fidelity Attribution for Quantum Compilers using HBR Decomposition.* [arXiv:2605.07876](https://arxiv.org/abs/2605.07876) (2026) | Attributes fidelity loss to decomposition, basis translation and routing across Qiskit, PennyLane and TKET; real IBM Fez runs included | Compile-stage attribution. A search snippet said it also sweeps 25 transpiler seeds, but the abstract does not mention seeds: read the paper before citing that |
| Qiskit docs, [SabreLayout](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.SabreLayout) | `layout_trials` runs seeded trials and keeps the one with the fewest swaps; when `SabreLayout` is called directly the default trial count is the local CPU count | Selection is by swap count, not by fidelity |
| Qiskit 2.3.0 source, `preset_passmanagers/builtin_plugins.py` (read locally) | The preset pass managers fix the trial count (5 at optimisation levels 0-1, 20 at levels 2-3) unless `QISKIT_SABRE_ALL_THREADS` is set | Each "seed" result in the PhD Paper 3 is the best of 5 internal trials at level 0; the paper should say so, with the Qiskit version used |

## Confirmed by several search results only (not opened in full)

- Harrigan et al. (Google Quantum AI), *QAOA of non-planar graph problems on a planar superconducting processor*,
  Nature Physics (2021), [arXiv:2004.04197](https://arxiv.org/abs/2004.04197): performance is size-independent for
  hardware-native problems and degrades with size for problems that need compilation.
- Pelofske, Bärtschi, Eidenbenz, *Quantum Annealing vs. QAOA: 127 Qubit Higher-Order Ising Problems on NISQ Computers*,
  [arXiv:2301.00520](https://arxiv.org/abs/2301.00520), later in npj Quantum Information (2024): QAOA p = 1, 2 on a 127-qubit
  IBM device; a follow-up reports the best p to be 2 or 3 on whole-chip QAOA.

## Seen only as search snippets: do not cite until read

I-QMapper (arXiv 2606.27508); a Quality Indicator Circuits layout method claiming to beat mapomatic (arXiv 2509.18679);
"From Circuits to Hardware" (arXiv 2607.11637); BAHAMAS control plane (arXiv 2608.28811), reportedly showing drift in the ranking of
QAOA parameter settings on IBM Fez and Torino; a depth-independent linear-chain ansatz run on ibm_kingston (arXiv 2509.17296);
and an unsourced preprint claim that p = 1 QAOA loses to a greedy heuristic on all instances.

## What this means for the research question

1. **Not new in outline.** Calibration-aware placement (mapomatic), best-of-trials routing (Qiskit) and hardware variability
   from mapping (Huo et al.) all exist. The question should be framed as an extension.
2. **A possible gap, unconfirmed.** No source found repeats the same QAOA instance under many compiler seeds on hardware and
   decomposes the spread of the measured approximation ratio into seed, shot noise and drift. Searches were limited.
3. **Design consequences.** Fix and record trial counts and the Qiskit version; compare the default fewest-swaps choice with a
   calibration-based score and with a random seed; measure drift with a repeated reference circuit; keep p <= 2; do not
   claim advantage (hardware QAOA at these depths is known to be noise-limited).
4. **Reading list before the interview:** Weidenfeller et al., Nation and Treinish, Huo et al., Harrigan et al.
