# Finace ML Validation — Hard Benchmark V2 Final Report

Generated: 2026-10-07T15:04:44.907417+00:00

## Architecture (unchanged)

- Regulatory Documents = SOURCE OF TRUTH
- RAG = REGULATORY EVIDENCE
- Rules = DETERMINISTIC CONTROLS
- ML = INDEPENDENT LEARNED PREDICTION
- Gemini = CONTEXTUAL REASONING
- XAI = MODEL/SURROGATE EXPLANATION

## A. Performance after removing lexical shortcuts?

- V2 status accuracy: `0.9726`
- V2 hard_benchmark_ready (shortcut QC): `True`
- Suspicious phrase count: `1`

## B. Drop V1 → V2

- V1: `0.9974`
- V2: `0.9726`
- Absolute drop: `0.0248`

## C. Unseen requirements

- V1 unseen: `{'status': 'measured', 'n': 852, 'status_accuracy': 0.9988, 'status_macro_f1': 0.9988, 'status_ece': 0.0173, 'status_roc_auc': 1.0, 'risk_accuracy': 0.9988, 'risk_macro_f1': 0.9988, 'risk_ece': 0.0173, 'per_domain_status_accuracy': {'AEPS': 1.0, 'CTS': 1.0, 'FASTAG': 1.0, 'IMPS': 1.0, 'KYC': 0.9167, 'NACH': 1.0, 'NFS': 1.0, 'RBI_MD': 1.0, 'RUPAY': 1.0}, 'per_difficulty_status_accuracy': {'easy': 0.9965, 'hard': 1.0, 'medium': 1.0}, 'per_risk_status_accuracy': {'HIGH': 1.0, 'LOW': 0.9965, 'MEDIUM': 1.0}}`
- V2 unseen: `{'status': 'measured', 'n': 1420, 'status_accuracy': 0.9824, 'status_macro_f1': 0.9827, 'status_ece': 0.024, 'status_roc_auc': 0.9990427699215637, 'risk_accuracy': 0.9824, 'risk_macro_f1': 0.9827, 'risk_ece': 0.024, 'per_domain_status_accuracy': {'AEPS': 1.0, 'CTS': 0.9719, 'FASTAG': 0.925, 'IMPS': 1.0, 'KYC': 1.0, 'NACH': 0.95, 'NFS': 1.0, 'RBI_MD': 0.985, 'RUPAY': 1.0}, 'per_difficulty_status_accuracy': {'hard': 0.9824}, 'per_risk_status_accuracy': {'HIGH': 0.9665, 'LOW': 0.9906, 'MEDIUM': 0.9953}}`

## D. Adversarial

`{'status': 'measured', 'n': 600, 'status_accuracy': 0.8217, 'status_macro_f1': 0.7584, 'status_ece': 0.2196, 'status_roc_auc': None, 'risk_accuracy': 0.8217, 'risk_macro_f1': 0.7584, 'risk_ece': 0.2196, 'per_domain_status_accuracy': {'AEPS': 0.8696, 'BHIM_AADHAR': 1.0, 'CTS': 0.8131, 'FASTAG': 0.8889}, 'per_difficulty_status_accuracy': {'hard': 0.8217}, 'per_risk_status_accuracy': {'HIGH': 0.465, 'LOW': 1.0}}`

## E. Human-validated gold

- Review status: `pending_human_review`
- Metrics: `{'status': 'pending', 'reason': 'No human-approved gold cases yet. Export review CSV and import decisions.'}`

## F. Feature drivers

See `feature_importance_v2.json`.

## G. ML vs Rules disagreement

See comparison artifact `risk_disagreement` section. Disagreement ≠ either side wrong.

## H. Limitations

- Template labels are not legal ground truth.
- Gold set remains pending until human/mentor approval.
- Gemini Finace assessment not invoked in compare (cost); rules used as Finace deterministic baseline.
- V2 reduces lexical shortcuts but residual structural cues remain (e.g. scenario_len_norm dominance).
- High V1 scores were development-benchmark artefacts from shortcut-prone templates.
- Adversarial set shows larger drops — treat V2 test accuracy as still partly template-separable.
- ML vs rules disagreement is expected; categories are heuristic, not correctness verdicts.
- ML never overrides RAG evidence, rules, Gemini, citations, or compliance score.

Full JSON: `C:\Users\Siddhant\OneDrive\Desktop\LY PROJECT\Finace\Finace\python-rag\ml_validation\data\reports\FINAL_REPORT_V2.json`