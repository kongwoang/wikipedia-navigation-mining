#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export MPLCONFIGDIR=.cache/matplotlib
mkdir -p "$MPLCONFIGDIR"
test -x .venv/bin/python || python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-study.lock
.venv/bin/python scripts/install_gensim_fix.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m wikinav.sources
if ! test -f data/processed/study-v2/manifest.json; then
    .venv/bin/python -m wikinav.study_data
fi
if ! test -f results/study-v2/completion.json; then
    .venv/bin/python -m wikinav.experiment --output results/study-v2
fi
if ! test -f reports/generated/summary.json; then
    .venv/bin/python -m wikinav.analysis --run results/study-v2
fi
.venv/bin/python -m wikinav.demo
echo 'Complete. Open reports/generated/demo.html and reports/REPORT.md.'
