"""Split reproducibility + leakage checks."""
import numpy as np

from ml.common import load_dataset, make_splits, DEFAULT_SEED


def test_split_reproducible(benchmark_csv):
    X, y, _ = load_dataset(benchmark_csv)
    a = make_splits(X, y, DEFAULT_SEED)
    b = make_splits(X, y, DEFAULT_SEED)
    for ia, ib in zip(a, b):
        assert np.array_equal(ia, ib)


def test_split_no_leakage(benchmark_csv):
    X, y, _ = load_dataset(benchmark_csv)
    tr, va, te = make_splits(X, y, DEFAULT_SEED)
    assert len(set(tr) & set(va)) == 0
    assert len(set(tr) & set(te)) == 0
    assert len(set(va) & set(te)) == 0


def test_split_proportions(benchmark_csv):
    X, y, _ = load_dataset(benchmark_csv)
    tr, va, te = make_splits(X, y, DEFAULT_SEED)
    total = len(y)
    assert abs(len(tr) / total - 0.7) < 0.01
    assert abs(len(va) / total - 0.15) < 0.01
    assert abs(len(te) / total - 0.15) < 0.01


def test_split_stratified(benchmark_csv):
    X, y, _ = load_dataset(benchmark_csv)
    tr, va, te = make_splits(X, y, DEFAULT_SEED)
    global_frac = {c: float((y == c).sum()) / len(y) for c in np.unique(y)}
    for name, idx in (("train", tr), ("val", va), ("test", te)):
        for c in global_frac:
            frac = float((y[idx] == c).sum()) / max(len(idx), 1)
            assert abs(frac - global_frac[c]) < 0.04, f"{name}/{c}: {frac} vs {global_frac[c]}"