#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export MPLCONFIGDIR=.cache/matplotlib
mkdir -p "$MPLCONFIGDIR"
test -x .venv/bin/python || python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-study.lock
.venv/bin/python scripts/install_gensim_fix.py
.venv/bin/python -m pip install -e . --no-deps --no-build-isolation
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m wikinav.sources
if ! test -f data/processed/study-v2/manifest.json; then
    .venv/bin/python -m wikinav.study_data
fi
study_run="${WIKINAV_RUN_DIR:-results/reproduction}"
study_report="${WIKINAV_REPORT_DIR:-reports/reproduced}"
if ! test -f "$study_run/completion.json"; then
    .venv/bin/python -m wikinav.experiment --output "$study_run"
fi
if ! test -f "$study_report/summary.json"; then
    .venv/bin/python -m wikinav.analysis --run "$study_run" --output "$study_report"
fi
.venv/bin/python -m wikinav.demo --folder "$study_report"
.venv/bin/python -m wikinav.verify_bundle --folder "$study_report" --seal
echo "Complete. Open $study_report/demo.html; compare tables against reports/generated."
