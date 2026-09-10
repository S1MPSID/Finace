#!/usr/bin/env bash
set -euo pipefail

echo "Python: $(python --version)"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo "Render build OK — fastembed only (no PyTorch)"
