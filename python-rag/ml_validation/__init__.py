"""
ML Validation Layer for Finace.

Architecture (additive — does not replace existing engines):

  REGULATIONS = source of truth  (Mongo chunks / documents)
  RAG         = evidence retrieval
  RULES       = deterministic controls
  ML          = learned compliance / risk prediction (this package)
  LLM         = reasoning (Gemini)
  XAI         = model explanation (distinct from surrogate SHAP/LIME)

Core principle: ML never invents, modifies, overrides, or replaces
regulatory clauses. Every requirement and every labelled case must
trace to an approved requirement bank entry grounded in a source chunk.
"""

__version__ = "0.1.0"
