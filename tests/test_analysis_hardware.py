"""Checks the pre-registered hardware analysis on SYNTHETIC counts built from the committed plan (never real data)."""
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from qaoa_study.analysis_hardware import analyse, load_runs
from qaoa_study.hardware import OUT, SHOTS, instances
from qaoa_study.qaoa import QAOA

PLAN = OUT / "plan.json"
pytestmark = pytest.mark.skipif(not PLAN.exists(), reason="hardware plan not generated")


def _synthetic(tmp_path: Path, fidelity) -> Path:
    """Counts from ideal*F + uniform*(1-F), where fidelity(circuit) -> F; shot noise only otherwise."""
    plan = json.loads(PLAN.read_text())
    shutil.copy(PLAN, tmp_path / "plan.json")
    insts = {(i["n"], i["graph"], i["p"]): i for i in instances()}
    rng = np.random.default_rng(1)
    results = []
    for c in plan["circuits"]:
        n, g, p, _ = c["key"]
        it = insts[(n, g, p)]
        ideal = QAOA(n, it["edges"]).probabilities(it["params"])
        f = fidelity(c)
        probs = f * ideal + (1 - f) / 2**n
        draws = rng.multinomial(SHOTS, probs / probs.sum())
        results.append({"position": c["position"], "counts": {format(i, f"0{n}b"): int(k) for i, k in enumerate(draws) if k}, "job_id": "synthetic", "job_usage_seconds": None})
    (tmp_path / "hardware_results.json").write_text(json.dumps({"plan_hash": plan["hash"], "backend": "synthetic", "jobs": [], "results": results}))
    return tmp_path


def test_shot_noise_only_gives_r_near_one_and_no_detection(tmp_path):
    text = analyse(load_runs(_synthetic(tmp_path, lambda c: 0.75), "results/raw"), tmp_path)
    pooled = next(line for line in text.splitlines() if line.startswith("| pooled"))
    r = float(pooled.split("|")[4].split("[")[0])
    assert 0.5 < r < 1.6
    assert "NOT DETECTED" in text


def test_an_injected_seed_effect_is_detected_and_predicted_by_the_cost_score(tmp_path):
    text = analyse(load_runs(_synthetic(tmp_path, lambda c: c["fidelity_score"]), "results/raw"), tmp_path)
    assert "DETECTED" in text and "NOT DETECTED" not in text
    assert "PREDICTIVE" in text and "NOT shown to be predictive" not in text
    assert "HELPS" in text
