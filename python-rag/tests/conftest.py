import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.common import default_dataset_csv


@pytest.fixture(scope="session")
def benchmark_csv() -> str:
    path = default_dataset_csv()
    assert os.path.exists(path), f"benchmark dataset missing: {path}"
    return path


@pytest.fixture(scope="session")
def predictor():
    from ml.predict import MLRiskPredictor

    p = MLRiskPredictor()
    assert p.available, "model artifacts missing; run `python -m ml.train` first"
    return p