"""
FINACE Machine-Learning Compliance Risk Prediction layer.

Modules
-------
feature_schema : canonical, documented feature schema (shared by train + serve)
features       : online feature extraction from existing pipeline outputs
labeling       : documented synthetic-label rulebook (benchmark only)
dataset        : reproducible synthetic benchmark dataset generator
train          : model training + selection + artifact/metadata export
predict        : lightweight online predictor used by the RAG pipeline
explain        : SHAP (+ optional LIME comparator) on the trained ML model
evaluate       : held-out evaluation metrics
stability      : repeated-scenario prediction/SHAP stability checks
"""