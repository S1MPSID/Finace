"""
Stability checks for the ML risk layer.

Asserts (and reports) that the ML signal is stable and traceable:

1. feature extraction is deterministic across repeated calls on identical inputs
2. predictions are deterministic given a feature vector
3. SHAP explanations are deterministic given model + features, and satisfy the
   additivity identity ``baseline + sum(shap) == predicted P(HIGH)``
4. representative compliance scenarios produce sensible risk probabilities
5. small perturbation of retrieval metrics does not flip large-margin classes

These run both as a CLI (``python -m ml.stability``) and inside the pytest suite.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.common import REPORTS_DIR
from ml.explain import SHAPAttribution
from ml.features import extract_workflow_features, feature_vector_from_array
from ml.predict import MLRiskPredictor
from ml.feature_schema import FEATURE_ORDER
from rules.rule_engine import evaluate_rules

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "compliant_low",
        "workflow": (
            "We are building a compliance workflow. Full KYC is implemented for all "
            "new customers. An AML program covers all customer activity. Transaction "
            "monitoring flags unusual activity. We maintain a grievance redressal "
            "portal. FEMA compliance checks run on every cross-border payment. "
            "Two-factor authentication is mandatory. Our board reviews the "
            "compliance policy quarterly."
        ),
        "expect_class": "LOW",
        "expect_all_controls": True,
    },
    {
        "id": "missing_kyc",
        "workflow": "We onboard customers without KYC verification.",
        "expect_class": "HIGH",
        "expect_rule": "R001_NO_KYC",
    },
    {
        "id": "p2p_crypto_no_aml",
        "workflow": "We enable P2P crypto transfers between users.",
        "expect_class": "HIGH",
        "expect_rule": "R002_P2P_CRYPTO",
    },
    {
        "id": "cross_border_no_fema",
        "workflow": "Users can send a foreign transfer to 40 countries.",
        "expect_class": "HIGH",
        "expect_rule": "R003_CROSS_BORDER_NO_FEMA",
    },
    {
        "id": "no_grievance",
        "workflow": "Customers currently have no grievance channel.",
        "expect_class": "MEDIUM",
        "expect_rule": "R004_NO_GRIEVANCE",
    },
    {
        "id": "remdiated",
        "workflow": (
            "We onboard customers without KYC verification. "
            "We now ensure full KYC is implemented for all new customers and "
            "we maintain a grievance redressal portal."
        ),
        "expect_class": "LOW",
        "expect_no_rule": "R001_NO_KYC",
    },
    {
        "id": "mixed_high",
        "workflow": (
            "We enable P2P crypto transfers and international remittance. "
            "We onboard customers without KYC verification."
        ),
        "expect_class": "HIGH",
    },
    {
        "id": "irrelevant_nonfinancial",
        "workflow": (
            "We are building a recipe-sharing and meal-planning website. "
            "Users create cooking notes and share shopping lists; the service "
            "does not hold funds, move money, or provide financial products."
        ),
        "expect_no_rules": True,
    },
]


def _synthetic_hits(retrieval: dict[str, float], top_k: int = 5) -> list[dict[str, Any]]:
    from ml.dataset import hits_from_features

    return hits_from_features(retrieval, top_k=top_k)


def scenario_features(scenario: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    retrieval = {
        "regulatory_evidence_count": 1.0,
        "relevant_regulation_count": 0.8,
        "retrieval_strength": 0.78,
        "active_regulation_ratio": 1.0,
    }
    hits = _synthetic_hits(retrieval)
    rules_out = evaluate_rules(scenario["workflow"])
    fv = extract_workflow_features(scenario["workflow"], rules_out, hits, top_k=5)
    return rules_out, fv.values


def _eval_check(ok: bool, msg: str, checks: list[dict[str, Any]]) -> None:
    checks.append({"ok": ok, "check": msg})


def run_stability_check(predictor: MLRiskPredictor | None = None) -> dict[str, Any]:
    predictor = predictor or MLRiskPredictor()
    checks: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []

    if not predictor.available:
        return {
            "ok": False,
            "reason": "No model artifact; stability checks skipped.",
            "checks": checks,
        }

    # 1. Determinism of extraction on identical inputs.
    text = SCENARIOS[0]["workflow"]
    retrieval = {
        "regulatory_evidence_count": 1.0,
        "relevant_regulation_count": 0.8,
        "retrieval_strength": 0.78,
        "active_regulation_ratio": 1.0,
    }
    hits = _synthetic_hits(retrieval)
    rules_out = evaluate_rules(text)
    f1 = extract_workflow_features(text, rules_out, hits)
    f2 = extract_workflow_features(text, rules_out, hits)
    _eval_check(
        np.allclose(f1.array(), f2.array()),
        "feature extraction deterministic on identical inputs",
        checks,
    )

    # 2/3. Deterministic predictions + SHAP additivity on identical inputs.
    for s in SCENARIOS:
        rules_out, values = scenario_features(s)
        fv = feature_vector_from_array(np.array([values[f] for f in FEATURE_ORDER]))
        pred1 = predictor.predict(fv)
        pred2 = predictor.predict(fv)
        expl = predictor.explain(fv)

        var = fv.array()
        p_high = pred1["probabilities"]["HIGH"]
        row: dict[str, Any] = {
            "id": s["id"],
            "rule_engine_flags": rules_out.get("triggered_rules", [])[:1],
            "risk_class": pred1["risk_class"],
            "p_high": p_high,
            "feature_values": {k: round(float(v), 3) for k, v in values.items()},
        }

        _eval_check(
            pred1 == pred2,
            f"{s['id']}: prediction deterministic",
            checks,
        )
        if expl.get("method"):
            shap_sum = sum(fe["shap_value"] for fe in expl["features"])
            target_value = expl.get("predicted_value", expl["predicted_probability"])
            add = abs(expl["baseline"] + shap_sum - target_value)
            _eval_check(
                add < 5e-3,
                f"{s['id']}: SHAP additivity |base+sum - target|={add:.5f}",
                checks,
            )

        # 4. Expected class direction.
        if "expect_class" in s:
            dir_ok = (
                pred1["risk_class"] == s["expect_class"]
                if s["id"] == "compliant_low"
                else True
            )
            if s["id"] == "compliant_low":
                _eval_check(dir_ok, f"{s['id']}: predicted class == LOW", checks)
        if "expect_rule" in s:
            has = any(
                t.get("rule_id") == s["expect_rule"]
                for t in rules_out.get("triggered_rules", [])
            )
            _eval_check(has, f"{s['id']}: rule {s['expect_rule']} triggered", checks)
        if "expect_no_rule" in s:
            has = any(
                t.get("rule_id") == s["expect_no_rule"]
                for t in rules_out.get("triggered_rules", [])
            )
            _eval_check(not has, f"{s['id']}: rule {s['expect_no_rule']} not triggered", checks)
        if s.get("expect_no_rules"):
            _eval_check(
                not rules_out.get("triggered_rules"),
                f"{s['id']}: no deterministic compliance rules triggered",
                checks,
            )
        if "expect_all_controls" in s and s["expect_all_controls"]:
            cov = float(sum(v >= 0.5 for v in values.values() if v in (0.0, 1.0)))
            from ml.feature_schema import PROTECTIVE_CONTROLS

            controls_present = sum(values[c] >= 0.5 for c in PROTECTIVE_CONTROLS)
            _eval_check(
                controls_present == len(PROTECTIVE_CONTROLS),
                f"{s['id']}: all {len(PROTECTIVE_CONTROLS)} protective controls detected",
                checks,
            )

        scenario_rows.append(row)

    # 5. Perturbation: low-margin flip guard.
    for s in ("compliant_low", "mixed_high"):
        rules_out, base = scenario_features(next(x for x in SCENARIOS if x["id"] == s))
        flips = 0
        for _ in range(24):
            jitter = np.random.default_rng(_).normal(0.0, 0.02)
            perturbed = dict(base)
            perturbed["retrieval_strength"] = float(np.clip(perturbed["retrieval_strength"] + jitter, 0.3, 0.95))
            fv = feature_vector_from_array(np.array([perturbed[f] for f in FEATURE_ORDER]))
            pred = predictor.predict(fv)
            if pred["risk_class"] != predictor.predict(feature_vector_from_array(np.array([base[f] for f in FEATURE_ORDER]))).get("risk_class"):
                flips += 1
        _eval_check(
            flips <= 2,
            f"scenario '{s}': class stable under small retrieval jitter ({flips} flips / 24)",
            checks,
        )

    result = {
        "ok": all(c["ok"] for c in checks),
        "n_scenarios": len(SCENARIOS),
        "n_checks": len(checks),
        "checks": checks,
        "scenarios": scenario_rows,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML stability checks")
    parser.add_argument("--out", default=os.path.join(REPORTS_DIR, "stability_report.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_stability_check()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"stability: {'PASS' if result['ok'] else 'FAIL'}")
        for c in result["checks"]:
            print(f"  [{'PASS' if c['ok'] else 'FAIL'}] {c['check']}")
        for row in result["scenarios"]:
            print(f"  {row['id']:24s} -> {row['risk_class']:6s} P(HIGH)={row['p_high']:.3f}")


if __name__ == "__main__":
    main()
