"""
Documented label rulebook for the SYNTHETIC benchmark dataset.

Purpose
-------
FINACE currently has no structured compliance dataset (the ~10.5k chunks in Mongo
are the regulatory knowledge base, not training labels). To build and validate
the ML risk-prediction machinery we generate a *development benchmark dataset*:

- labels are computed from a fixed, documented, weighted rulebook defined below
- a latent component (unobserved factor) plus Gaussian noise **by design** makes
  the mapping from observed features to label imperfect, so the models have a real
  learning problem (non-trivial AUC) instead of being able to perfectly
  re-derive the label from the features
- no LLM output is ever used as ground truth

This dataset is explicitly NOT market/regulator ground truth. It exists to
exercise the training/evaluation/SHAP/serving stack and to sanity-check the
feature pipeline. Any production risk decisions must be validated against real
labelled workflows before the model is relied upon.
"""
from __future__ import annotations

import numpy as np

from ml.feature_schema import (
    EXPOSURE_FEATURES,
    PROTECTIVE_CONTROLS,
    RISK_LEVELS,
)

# Number of protective controls the rulebook rewards.
_CONTROL_N = len(PROTECTIVE_CONTROLS)

# Raw weights per trigger (documented, tuned so class priors are balanced-ish).
W_HIGH_GAP = 0.28      # each triggered HIGH-risk gap rule
W_MEDIUM_GAP = 0.13    # each triggered MEDIUM-risk gap rule
W_EXPOSURE = 0.08      # each active exposure domain (cross-border / p2p-crypto)
W_MISSING_CONTROL = 0.035  # each absent protective control
W_INACTIVE_EVIDENCE = 0.03  # penalize low active_regulation_ratio
BASE_RISK = 0.10

# Unobserved/latent variation the model cannot see (sd), plus irreducible noise.
LATENT_STD = 0.10
NOISE_STD = 0.06

# Class thresholds on the latent risk score z (documented).
LOW_UPPER = 0.38
MEDIUM_UPPER = 0.62


class RulebookResult:
    def __init__(self, z: float, label: str, components: dict[str, float], seed: int):
        self.z = float(z)
        self.label = label
        self.components = components
        self.seed = seed

    def to_dict(self) -> dict:
        return {
            "latent_risk_score": round(self.z, 6),
            "label": self.label,
            "components": {k: round(v, 6) for k, v in self.components.items()},
            "seed": self.seed,
        }


def risk_index(label: str) -> int:
    return RISK_LEVELS.index(label)


def label_from_risk_score(z: float) -> str:
    if z < LOW_UPPER:
        return "LOW"
    if z < MEDIUM_UPPER:
        return "MEDIUM"
    return "HIGH"


def compute_label(
    feature_values: dict[str, float],
    triggered_rule_risk_levels: list[str],
    rng: np.random.Generator,
    *,
    seed: int | None = None,
) -> RulebookResult:
    """
    Compute the documented synthetic label for one feature vector.

    Args:
        feature_values: canonical feature dict (rule:, control, exposure, retrieval).
        triggered_rule_risk_levels: risk levels of the triggered rules in this
            scenario (HIGH/MEDIUM) as produced by the actual rule engine.
        rng: seeded random generator for the latent + noise draws.
    """
    high_gaps = sum(1 for lv in triggered_rule_risk_levels if lv == "HIGH")
    medium_gaps = sum(1 for lv in triggered_rule_risk_levels if lv == "MEDIUM")
    exposure = sum(1 for f in EXPOSURE_FEATURES if feature_values.get(f, 0.0) >= 0.5)
    missing_controls = sum(
        1 for c in PROTECTIVE_CONTROLS if feature_values.get(c, 0.0) < 0.5
    )
    active_ratio = float(np.clip(feature_values.get("active_regulation_ratio", 1.0), 0.0, 1.0))

    components = {
        "high_gap_rules": float(high_gaps),
        "medium_gap_rules": float(medium_gaps),
        "exposures": float(exposure),
        "missing_controls": float(missing_controls),
        "inactive_evidence": float(1.0 - active_ratio),
    }

    latent = float(rng.normal(0.0, LATENT_STD))
    noise = float(rng.normal(0.0, NOISE_STD))

    z = (
        BASE_RISK
        + W_HIGH_GAP * high_gaps
        + W_MEDIUM_GAP * medium_gaps
        + W_EXPOSURE * exposure
        + W_MISSING_CONTROL * missing_controls
        + W_INACTIVE_EVIDENCE * (1.0 - active_ratio)
        + latent
        + noise
    )
    z = float(np.clip(z, 0.0, 1.0))

    return RulebookResult(z=z, label=label_from_risk_score(z), components=components, seed=seed or 0)


def rulebook_documentation() -> dict:
    return {
        "purpose": (
            "Synthetic benchmark/development labels for exercising the ML risk layer. "
            "Not real regulatory ground truth."
        ),
        "equation": (
            "z = BASE + W_HIGH_GAP*high_gaps + W_MEDIUM_GAP*medium_gaps "
            "+ W_EXPOSURE*exposures + W_MISSING_CONTROL*missing_controls "
            "+ W_INACTIVE_EVIDENCE*(1-active_ratio) + latent + noise"
        ),
        "weights": {
            "BASE_RISK": BASE_RISK,
            "W_HIGH_GAP": W_HIGH_GAP,
            "W_MEDIUM_GAP": W_MEDIUM_GAP,
            "W_EXPOSURE": W_EXPOSURE,
            "W_MISSING_CONTROL": W_MISSING_CONTROL,
            "W_INACTIVE_EVIDENCE": W_INACTIVE_EVIDENCE,
            "LATENT_STD": LATENT_STD,
            "NOISE_STD": NOISE_STD,
        },
        "thresholds": {
            "LOW": f"[0, {LOW_UPPER})",
            "MEDIUM": f"[{LOW_UPPER}, {MEDIUM_UPPER})",
            "HIGH": f"[{MEDIUM_UPPER}, 1]",
        },
        "on_label_distribution": (
            "Because z starts at BASE_RISK=0.10 and only gains ~0.28 per HIGH gap, "
            "scenarios with no triggered rules and good controls land in LOW, while "
            "scenarios with multiple HIGH gaps land in HIGH; the boundary band is noisy."
        ),
    }