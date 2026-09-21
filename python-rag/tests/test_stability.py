"""Stability gate: all checks from `python -m ml.stability` must pass."""
from ml.stability import run_stability_check, SCENARIOS


def test_stability_gate(predictor):
    result = run_stability_check(predictor)
    assert result["ok"], "stability checks failed:\n" + "\n".join(
        f"  [FAIL] {c['check']}" for c in result["checks"] if not c["ok"]
    )
    assert result["n_checks"] >= 20
    assert len(result["scenarios"]) == len(SCENARIOS)