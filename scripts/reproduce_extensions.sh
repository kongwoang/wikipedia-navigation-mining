#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export MPLCONFIGDIR=.cache/matplotlib
mkdir -p "$MPLCONFIGDIR"
# The base script bootstraps dependencies and pinned historical data if needed.
if ! test -x .venv/bin/python || ! test -f data/processed/study-v2/manifest.json; then
    sh scripts/reproduce.sh
fi
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/acquire_extension.py
.venv/bin/python -m wikinav.extension_data
if ! test -f data/processed/full-extension/pilot.json; then
    .venv/bin/python scripts/full_graph_pilot.py
fi
extension_run="${WIKINAV_EXTENSION_RUN:-results/extensions-reproduction}"
extension_report="${WIKINAV_EXTENSION_REPORT:-reports/extensions/reproduced}"
# Run sequentially to keep peak concurrent memory predictable on student laptops.
for stage in boundary rolling null; do
    .venv/bin/python -m wikinav.extension_experiment "$stage" --output "$extension_run/$stage"
done
if ! test -f "$extension_report/bundle_manifest.json"; then
    .venv/bin/python scripts/build_extension_report.py --run "$extension_run" --output "$extension_report"
fi
.venv/bin/python -m wikinav.verify_extensions --folder "$extension_report"
.venv/bin/python scripts/build_extension_writeup.py --folder "$extension_report" --output "$extension_report/writeup"
echo "Complete. Extension figures, tables, frozen payloads and demo: $extension_report"
