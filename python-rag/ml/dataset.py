"""
Synthetic benchmark dataset generator for the ML risk layer.

Each row is synthesised in a way that guarantees **train/serve parity**:

1. sample control / exposure flags + retrieval metrics from a documented distribution
2. compose a realistic ``workflow_description`` from the flag-matched vocabulary
3. run the REAL deterministic rule engine (``evaluate_rules``) on that text
4. extract the canonical ML feature vector with the SAME function used online
5. compute the documented synthetic label from the extracted features

The label is therefore a noisy transform of the features (see ``ml/labeling.py``),
with the rule-trigger features produced by the exact engine deployed in production.

Salient caveats (also recorded in the metadata):
- output is a DEVELOPMENT benchmark, NOT regulatory ground truth
- retrieval metrics are sampled from a documented distribution (they are
  measured live at inference time; they cannot be derived from text alone)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.feature_schema import (
    EXPOSURE_FEATURES,
    FEATURE_ORDER,
    PROTECTIVE_CONTROLS,
    SCHEMA_VERSION,
)
from ml.features import extract_workflow_features
from ml.labeling import compute_label, rulebook_documentation

DEFAULT_N = 2400
DEFAULT_SEED = 20260919


# ── Feature flag vocabulary ────────────────────────────────────────────────────
# Every sentence is crafted so the rule engine and the stance-aware detector
# interpret the row exactly as intended (verified by the parity check in main()).

_CONTROL_SENTENCES: dict[str, dict[str, list[str]]] = {
    "kyc_present": {
        "present": [
            "Full KYC is implemented for all new customers.",
            "All customers complete KYC verification before onboarding.",
            "We enforce mandatory KYC checks at account opening.",
            "KYC is enabled with Aadhaar-based eKYC verification.",
        ],
        "absent": [
            "We onboard customers without KYC verification.",
            "New accounts can be opened with no KYC checks.",
            "We skip KYC for quick-serve wallet accounts.",
        ],
    },
    "aml_present": {
        "present": [
            "An AML program covers all customer activity.",
            "We run anti-money laundering screening on every transaction.",
            "Enhanced due diligence is applied to higher-risk customers.",
            "Our AML unit checks all on-boarded customers.",
        ],
        "absent": [
            "We do not yet conduct any customer screening.",
            "Customer screening has not been started.",
        ],
    },
    "transaction_monitoring": {
        "present": [
            "Transaction monitoring flags unusual activity in real time.",
            "Ongoing due diligence is carried out on accounts.",
            "Suspicious transaction reports are filed as required.",
            "We screen every transaction and report STRs.",
        ],
        "absent": [
            "We do not run ongoing checks on customer accounts.",
            "Account activity is not continuously reviewed.",
        ],
    },
    "grievance_mechanism": {
        "present": [
            "We maintain a grievance redressal portal.",
            "A dedicated complaint handling process routes customer issues.",
            "All customer complaints are logged in our grievance mechanism.",
        ],
        "absent": [
            "Customers currently have no grievance channel.",
            "There is no complaint desk for customers yet.",
        ],
    },
    "fema_controls": {
        "present": [
            "FEMA compliance checks run on every cross-border payment.",
            "Forex declaration and RBI reporting are part of the flow.",
            "FX compliance is reviewed by our treasury team.",
        ],
        "absent": [
            "We do not run a regime-specific review for non-domestic flows.",
            "Non-domestic payments are not subject to a dedicated review.",
        ],
    },
    "authentication_control": {
        "present": [
            "Two-factor authentication is mandatory for every login.",
            "Users must pass OTP verification to authorize payments.",
            "Multi-factor authentication protects all sensitive actions.",
        ],
        "absent": [
            "Accounts do not yet require two-factor authentication.",
        ],
    },
    "compliance_policy_present": {
        "present": [
            "Our board reviews the compliance policy quarterly.",
            "A documented compliance policy governs the product.",
            "Compliance officers oversee adherence to the policy document.",
        ],
        "absent": [
            "We have not published a compliance policy yet.",
        ],
    },
}

_EXPOSURE_SENTENCES: dict[str, dict[str, list[str]]] = {
    "cross_border_activity": {
        "present": [
            "International remittance flows are supported for our users.",
            "Users can send a foreign transfer to 40 countries.",
            "We process cross-border remittances for corporate customers.",
            "Customers initiate foreign transfers from the app.",
        ],
    },
    "p2p_crypto_activity": {
        "present": [
            "We enable P2P crypto transfers between users.",
            "The platform supports virtual asset trading.",
            "Users can trade via a P2P crypto exchange.",
            "Bitcoin and virtual asset trading are available.",
        ],
    },
}

_OPENING_SENTENCES = [
    "We are building a compliance workflow for a new financial product.",
    "This is the current operating model for our digital payments service.",
    "Our onboarding flow is described below.",
    "We are documenting how our product currently operates.",
]


def _pick(rng: np.random.Generator, options: list[str]) -> str:
    return options[int(rng.integers(0, len(options)))]


def _sample_retrieval_metrics(rng: np.random.Generator, top_k: int = 5) -> dict[str, float]:
    """Sample raw retrieval metrics from a documented distribution.

    At inference time these come from ``LocalRetriever.search``; the synthetic
    rows use roughly the shape the live retriever produces for focused compliance
    queries (typically 4-5 strong hits, nearly all active).
    """
    n_hits = int(rng.integers(4, top_k + 1))
    distinct = int(rng.integers(max(1, n_hits - 1), n_hits + 1))
    strength = float(np.clip(rng.normal(0.72, 0.08), 0.1, 0.9))
    if rng.random() > 0.15:
        active_count = n_hits
    else:
        active_count = int(rng.integers(max(1, int(0.4 * n_hits)), n_hits))
    return {
        "regulatory_evidence_count": min(n_hits / top_k, 1.0),
        "relevant_regulation_count": min(distinct / top_k, 1.0),
        "retrieval_strength": strength,
        "active_regulation_ratio": min(active_count / max(n_hits, 1), 1.0),
    }


def hits_from_features(features: dict[str, float], top_k: int = 5) -> list[dict[str, Any]]:
    """Deterministically rebuild synthetic hits from the (extracted) retrieval features.

    The mean of the emitted scores equals ``retrieval_strength`` exactly and the
    emitted status counts equal ``active_regulation_ratio`` exactly, so re-running
    the live feature extractor over these hits reproduces the stored features bit
    for bit (train/serve parity).
    """
    n = int(round(features["regulatory_evidence_count"] * top_k))
    distinct = int(round(features["relevant_regulation_count"] * top_k))
    base = float(features["retrieval_strength"])
    active = int(round(features["active_regulation_ratio"] * n))

    hits: list[dict[str, Any]] = []
    for i in range(n):
        offset = 0.0 if n <= 1 else 0.01 * (i - (n - 1) / 2)
        hits.append(
            {
                "document_id": f"RBI/2024/SYN-{i % max(distinct, 1) + 1}",
                "score": float(np.clip(base + offset, 0.0, 1.0)),
                "metadata": {
                    "status": "active" if i < active else "superseded",
                    "regulator": "RBI",
                },
            }
        )
    return hits


def _sample_flags(rng: np.random.Generator) -> tuple[dict[str, bool], dict[str, bool]]:
    """Sample protective-control and exposure flags with a documented distribution."""
    if rng.random() < 0.14:
        # A clean low-risk scenario: all controls present, no exposure.
        controls = {c: True for c in PROTECTIVE_CONTROLS}
        exposures = {e: False for e in EXPOSURE_FEATURES}
        return controls, exposures

    controls = {c: rng.random() < 0.5 for c in PROTECTIVE_CONTROLS}
    exposures = {
        "cross_border_activity": rng.random() < 0.38,
        "p2p_crypto_activity": rng.random() < 0.32,
    }
    return controls, exposures


def compose_workflow(flags: dict[str, bool], rng: np.random.Generator) -> str:
    """Build a workflow_description whose engine interpretation matches `flags`."""
    parts: list[str] = [_pick(rng, _OPENING_SENTENCES)]

    for ctrl in PROTECTIVE_CONTROLS:
        vocab = _CONTROL_SENTENCES[ctrl]
        block = vocab["present"] if flags[ctrl] else vocab["absent"]
        if block:
            parts.append(_pick(rng, block))

    for exp in EXPOSURE_FEATURES:
        if flags[exp]:
            parts.append(_pick(rng, _EXPOSURE_SENTENCES[exp]["present"]))

    return " ".join(parts)


def generate_row(
    rng: np.random.Generator,
    top_k: int = 5,
    controls: dict[str, bool] | None = None,
    exposures: dict[str, bool] | None = None,
) -> dict[str, Any]:
    if controls is None or exposures is None:
        sampled_controls, sampled_exposures = _sample_flags(rng)
        if controls is None:
            controls = sampled_controls
        if exposures is None:
            exposures = sampled_exposures
    workflow = compose_workflow({**controls, **exposures}, rng)
    retrieval = _sample_retrieval_metrics(rng, top_k=top_k)
    hits = hits_from_features(retrieval, top_k=top_k)

    from rules.rule_engine import evaluate_rules

    rules_out = evaluate_rules(workflow)
    trigger_levels = [
        item.get("risk_level", "MEDIUM")
        for item in rules_out.get("triggered_rules", [])
        if item.get("rule_id")
    ]

    fv = extract_workflow_features(
        workflow_text=workflow,
        rules_out=rules_out,
        retrieval_hits=hits,
        top_k=top_k,
    )

    seed_draw = int(rng.integers(0, 2**31))
    result = compute_label(
        feature_values=fv.values,
        triggered_rule_risk_levels=trigger_levels,
        rng=rng,
        seed=seed_draw,
    )

    return {
        "workflow_description": workflow,
        "label": result.label,
        "latent_risk_score": result.z,
        "triggered_rule_ids": ",".join(
            item.get("rule_id", "") for item in rules_out.get("triggered_rules", [])
        ),
        "intended_controls": ",".join(c for c, v in controls.items() if v),
        "intended_exposures": ",".join(e for e, v in exposures.items() if v),
        **{f: fv.values[f] for f in FEATURE_ORDER},
    }


def _rules_hash() -> str:
    import rules.rules_config as rc

    payload = json.dumps(rc.RULES, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def generate_dataset(
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
    top_k: int = 5,
    out_dir: str | None = None,
) -> tuple[str, str, dict]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = [generate_row(rng, top_k=top_k) for _ in range(n)]

    out_dir = out_dir or os.path.join(ROOT, "ml", "datasets")
    os.makedirs(out_dir, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    version_tag = f"v1-{seed}-{n}"
    csv_path = os.path.join(out_dir, f"risk_benchmark_{version_tag}.csv")
    meta_path = os.path.join(out_dir, f"risk_benchmark_{version_tag}_meta.json")

    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    labels = Counter(r["label"] for r in rows)
    triggered = Counter(
        token
        for r in rows
        for token in r["triggered_rule_ids"].split(",")
        if token
    )

    metadata: dict[str, Any] = {
        "purpose": (
            "SYNTHETIC development benchmark dataset for the FINACE ML risk "
            "prediction layer. NOT regulatory ground truth."
        ),
        "created_utc": stamp,
        "seed": seed,
        "n_rows": n,
        "top_k": top_k,
        "schema_version": SCHEMA_VERSION,
        "features": FEATURE_ORDER,
        "label_distribution": dict(labels),
        "rule_trigger_distribution": dict(triggered),
        "label_rulebook": rulebook_documentation(),
        "rules_hash": _rules_hash(),
        "notes": [
            "workflow_description is generated from a flag-matched vocabulary so the "
            "live rule engine and the online feature extractor reproduce the row.",
            "retrieval metrics are sampled (synthetic); at serving time they are "
            "measured from LocalRetriever.search output.",
        ],
    }
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    return csv_path, meta_path, metadata


def parity_check(csv_path: str, top_k: int = 5) -> list[str]:
    """Re-run the real online extractor over stored rows; report any mismatches."""
    from rules.rule_engine import evaluate_rules

    mismatches: list[str] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            retrieval = {
                f: float(row[f])
                for f in ("regulatory_evidence_count", "relevant_regulation_count",
                          "retrieval_strength", "active_regulation_ratio")
            }
            hits = hits_from_features(retrieval, top_k=top_k)
            fv = extract_workflow_features(
                workflow_text=row["workflow_description"],
                rules_out=evaluate_rules(row["workflow_description"]),
                retrieval_hits=hits,
                top_k=top_k,
            )
            bad = [f for f in FEATURE_ORDER if abs(fv.values[f] - float(row[f])) > 1e-9]
            if bad:
                mismatches.append(f"row {i}: {bad}")
    return mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic ML risk benchmark dataset")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--parity-check", action="store_true", help="Verify train/serve parity after generation")
    args = parser.parse_args()

    csv_path, meta_path, meta = generate_dataset(
        n=args.n, seed=args.seed, top_k=args.top_k
    )
    print(f"dataset written to {csv_path}")
    print(f"metadata written to {meta_path}")
    print("label distribution:", json.dumps(meta["label_distribution"]))
    print("rule triggers:", json.dumps(meta["rule_trigger_distribution"]))

    mismatch = parity_check(csv_path, top_k=args.top_k)
    if mismatch:
        print(f"PARITY FAILED: {len(mismatch)} rows mismatch, e.g. {mismatch[:5]}")
        sys.exit(1)
    print("train/serve parity OK on every row")


if __name__ == "__main__":
    main()
