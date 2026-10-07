# `ml_validation` — Finace ML Validation Layer

Additive package. Does **not** replace RAG, rules, Gemini, or existing `python-rag/ml/` risk layer.

## Quick start

```powershell
cd python-rag
.\.venv\Scripts\Activate.ps1
python -m ml_validation.cli pipeline --extract
```

Docs:

- `docs/ml_validation/REQUIREMENT_BANK.md`
- `docs/ml_validation/METHODOLOGY.md`
- `docs/ml_validation/PIPELINE.md`

## Live API field

`/query` and `/analyze` responses include `ml_validation` (status + risk + probabilities + model-local explanation).  
Existing `ml_risk`, `xai`, `rules`, and compliance score are unchanged.
