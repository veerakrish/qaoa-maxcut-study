"""Pre-registered hardware batch (docs/PREREGISTRATION_HARDWARE.md): plan, pre-flight gates, submit, collect.

    python -m qaoa_study.hardware plan --backend ibm_marrakesh     # compile + gates + save the plan; submits nothing
    python -m qaoa_study.hardware submit --plan-hash <hash>        # submit exactly the saved, approved plan
    python -m qaoa_study.hardware collect                          # fetch results of the submitted job(s)

Run with an interpreter that has qiskit-ibm-runtime. The plan step only reads backend data (target, calibration); it never creates a job.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.quantum_info import Statevector
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from .circuit import qaoa_circuit
from .graphs import cubic_instances
from .qaoa import QAOA

SIZES, GRAPHS_PER_SIZE, DEPTHS, SEEDS = (8, 10), 5, (1, 2), range(5)
OPT_LEVEL, SHOTS, REPEATS, ORDER_SEED = 3, 4096, 10, 20261029
REFERENCE = (8, 0, 1, 0)           # (n, graph, p, seed) of the compiled circuit repeated to measure drift
REP_DELAY_S = 250e-6               # assumed repetition delay, used only for the time estimate
OUT = Path("results/hardware")


def instances(raw_dir: str = "results/raw") -> list[dict]:
    """The 10 graphs x 2 depths, with the ideal-arm best parameters from the simulation phase."""
    out = []
    for n in SIZES:
        for idx, edges in enumerate(cubic_instances(n)[:GRAPHS_PER_SIZE]):
            d = json.loads(Path(raw_dir, f"n{n}_i{idx:02d}.json").read_text())
            assert [tuple(e) for e in d["edges"]] == [tuple(e) for e in edges], "graph differs from the simulation phase"
            model = QAOA(n, edges)
            for p in DEPTHS:
                best = max((r for r in d["runs"] if r["mode"] == "ideal" and r["p"] == p), key=lambda r: r["ratio"])
                assert abs(model.expectation(best["params"]) / model.cmax - best["ratio"]) < 1e-9, "stored parameters do not reproduce the stored ratio"
                out.append({"n": n, "graph": idx, "p": p, "edges": edges, "params": best["params"],
                            "ideal_ratio": best["ratio"], "cmax": model.cmax})
    return out


def circuit_stats(isa: QuantumCircuit, target) -> dict:
    """Compiled-circuit statistics and the cost score: product over two-qubit gates and readouts of (1 - error)."""
    n2q, log_f, measured, used = 0, 0.0, [], set()
    for inst in isa.data:
        name = inst.operation.name
        if name == "barrier":
            continue
        qs = tuple(isa.find_bit(q).index for q in inst.qubits)
        used.update(qs)
        if name == "measure":
            measured.append(qs[0])
        elif len(qs) == 2:
            n2q += 1
            log_f += np.log1p(-target[name][qs].error)
    for q in measured:
        log_f += np.log1p(-target["measure"][(q,)].error)
    return {"n2q": n2q, "depth": isa.depth(), "depth2q": isa.depth(lambda i: len(i.qubits) == 2),
            "active_qubits": len(used), "log_fidelity": float(log_f), "fidelity_score": float(np.exp(log_f))}


def noiseless_distribution(isa: QuantumCircuit, n: int) -> np.ndarray:
    """Output distribution of the compiled circuit over its n measured bits, simulated on its active qubits only."""
    used = sorted({isa.find_bit(q).index for i in isa.data if i.operation.name != "barrier" for q in i.qubits})
    if len(used) > 24:
        raise RuntimeError(f"{len(used)} active qubits: too many to verify by statevector")
    pos = {q: k for k, q in enumerate(used)}
    reduced, meas = QuantumCircuit(len(used), global_phase=isa.global_phase), {}
    for inst in isa.data:
        name = inst.operation.name
        if name == "barrier":
            continue
        qs = [pos[isa.find_bit(q).index] for q in inst.qubits]
        if name == "measure":
            meas[isa.find_bit(inst.clbits[0]).index] = qs[0]
        else:
            reduced.append(inst.operation, qs)
    return Statevector(reduced).probabilities([meas[j] for j in range(n)])


def build_plan(backend) -> tuple[dict, list]:
    insts = instances()
    compiled = []
    for it in insts:
        circuit = qaoa_circuit(it["n"], it["edges"], it["params"], measure=True)
        ideal = QAOA(it["n"], it["edges"]).probabilities(it["params"])
        for seed in SEEDS:
            isa = generate_preset_pass_manager(optimization_level=OPT_LEVEL, backend=backend, seed_transpiler=seed).run(circuit)
            tvd = 0.5 * float(np.abs(noiseless_distribution(isa, it["n"]) - ideal).sum())
            compiled.append({"key": [it["n"], it["graph"], it["p"], seed], "ideal_ratio": it["ideal_ratio"], "cmax": it["cmax"],
                             "tvd_vs_ideal": tvd, **circuit_stats(isa, backend.target), "_isa": isa})
    ref = next(c for c in compiled if tuple(c["key"]) == REFERENCE)
    pool = compiled + [dict(ref, repeat=True) for _ in range(REPEATS)]
    order = np.random.default_rng(ORDER_SEED).permutation(len(pool))
    run_list = [pool[i] for i in order]
    for pos, c in enumerate(run_list):
        c["position"] = pos
    return {"circuits": [{k: v for k, v in c.items() if k != "_isa"} for c in run_list]}, [c["_isa"] for c in run_list]


def estimated_qpu_seconds(isas, target) -> tuple[float, float]:
    """(low, high): shots x circuit duration, and shots x (duration + repetition delay) with a 25% allowance."""
    try:
        durations = [isa.estimate_duration(target) for isa in isas]
    except Exception:
        durations = [30e-6] * len(isas)
    low = SHOTS * sum(durations)
    return low, 1.25 * SHOTS * sum(d + REP_DELAY_S for d in durations)


def plan_hash(plan: dict) -> str:
    core = {"backend": plan["backend"], "shots": plan["shots"], "circuits": [(c["position"], c["key"], c["n2q"], c["depth"]) for c in plan["circuits"]]}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:12]


def cmd_plan(args):
    from qiskit_ibm_runtime import QiskitRuntimeService
    import qiskit, qiskit_ibm_runtime
    service = QiskitRuntimeService()
    backend = service.backend(args.backend)
    status = backend.status()
    plan, isas = build_plan(backend)
    low, high = estimated_qpu_seconds(isas, backend.target)
    try:
        calibration = str(backend.properties().last_update_date)
    except Exception:
        calibration = "unavailable"
    plan.update({"backend": backend.name, "n_qubits": backend.num_qubits, "pending_jobs_at_planning": status.pending_jobs,
                 "calibration_timestamp": calibration, "max_circuits": getattr(backend, "max_circuits", None),
                 "shots": SHOTS, "optimization_level": OPT_LEVEL, "order_seed": ORDER_SEED, "planned_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
                 "versions": {"qiskit": qiskit.__version__, "qiskit_ibm_runtime": qiskit_ibm_runtime.__version__},
                 "estimated_qpu_seconds": {"low": low, "high": high}})
    plan["hash"] = plan_hash(plan)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "plan.json").write_text(json.dumps(plan, indent=1))
    with open(OUT / "plan.qpy", "wb") as f:
        qpy.dump(isas, f)

    cs = plan["circuits"]
    worst_tvd = max(c["tvd_vs_ideal"] for c in cs)
    unique = len({tuple(c["key"]) for c in cs})
    print(f"backend {plan['backend']} ({plan['n_qubits']} qubits), {status.pending_jobs} jobs queued, calibration {calibration}")
    print(f"circuits: {len(cs)} to run ({unique} distinct compiled + {REPEATS} reference repeats), {SHOTS} shots each, level {OPT_LEVEL}")
    print(f"two-qubit gates per circuit: min {min(c['n2q'] for c in cs)}, median {int(np.median([c['n2q'] for c in cs]))}, max {max(c['n2q'] for c in cs)}")
    print(f"active qubits: max {max(c['active_qubits'] for c in cs)}; cost score F: min {min(c['fidelity_score'] for c in cs):.3f}, max {max(c['fidelity_score'] for c in cs):.3f}")
    print(f"max_circuits per job on this backend: {plan['max_circuits']}")
    print(f"GATE 1 noiseless equivalence: worst total-variation distance {worst_tvd:.2e} -> {'PASS' if worst_tvd < 1e-6 else 'FAIL'}")
    print(f"GATE 3 estimated QPU time: {low:.0f} to {high:.0f} s (cap 300 s; open-plan allowance 600 s) -> {'WITHIN CAP' if high <= 300 else 'OVER CAP'}")
    print(f"plan hash: {plan['hash']}   (saved to {OUT / 'plan.json'} and plan.qpy; nothing submitted)")


def cmd_submit(args):
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    plan = json.loads((OUT / "plan.json").read_text())
    if plan_hash(plan) != plan["hash"] or args.plan_hash != plan["hash"]:
        raise SystemExit(f"plan hash mismatch (saved {plan['hash']}, given {args.plan_hash}): refusing to submit")
    with open(OUT / "plan.qpy", "rb") as f:
        isas = qpy.load(f)
    backend = QiskitRuntimeService().backend(plan["backend"])
    chunk = plan["max_circuits"] or len(isas)
    jobs, results = [], []
    for start in range(0, len(isas), chunk):
        batch = isas[start:start + chunk]
        job = SamplerV2(mode=backend).run([(isa, None, SHOTS) for isa in batch])
        jobs.append({"job_id": job.job_id(), "first_position": start, "n_circuits": len(batch), "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S %z")})
        (OUT / "submitted.json").write_text(json.dumps({"plan_hash": plan["hash"], "backend": plan["backend"], "jobs": jobs}, indent=1))
        print("submitted job", job.job_id(), flush=True)
    for j in jobs:
        results += _fetch(QiskitRuntimeService(), j["job_id"], j["first_position"])
    _save(plan, jobs, results)


def _fetch(service, job_id: str, first_position: int) -> list[dict]:
    job = service.job(job_id)
    result = job.result()
    usage = None
    try:
        usage = job.usage()
    except Exception:
        pass
    return [{"position": first_position + i, "counts": pub.data.meas.get_counts(), "job_id": job_id, "job_usage_seconds": usage}
            for i, pub in enumerate(result)]


def _save(plan: dict, jobs: list, results: list) -> None:
    (OUT / "hardware_results.json").write_text(json.dumps({"plan_hash": plan["hash"], "backend": plan["backend"], "jobs": jobs, "results": results}))
    print(f"saved {len(results)} circuit results to {OUT / 'hardware_results.json'}")


def cmd_collect(args):
    from qiskit_ibm_runtime import QiskitRuntimeService
    plan = json.loads((OUT / "plan.json").read_text())
    submitted = json.loads((OUT / "submitted.json").read_text())
    service = QiskitRuntimeService()
    results = []
    for j in submitted["jobs"]:
        results += _fetch(service, j["job_id"], j["first_position"])
    _save(plan, submitted["jobs"], results)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan").add_argument("--backend", required=True)
    sub.add_parser("submit").add_argument("--plan-hash", required=True)
    sub.add_parser("collect")
    args = ap.parse_args(argv)
    {"plan": cmd_plan, "submit": cmd_submit, "collect": cmd_collect}[args.cmd](args)


if __name__ == "__main__":
    main()
