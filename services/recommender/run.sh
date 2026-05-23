#!/usr/bin/env bash
# Usage: ./run.sh [--dev]
#   SURVEYS_DIR      — pending survey subdirs written by intake (default /var/ponderosa/surveys/pending)
#   PROCESSED_DIR    — destination after recommender finishes (default /var/ponderosa/surveys/processed)
#   RECOMMENDER_PIPE — named pipe written by intake (default /var/ponderosa/pipes/recommender)
#   PRESENTER_PIPE   — named pipe read by presenter (default /var/ponderosa/pipes/presenter)

set -e

cd "$(dirname "$0")"

if [[ "$1" == "--dev" ]]; then
  SURVEYS_DIR="${SURVEYS_DIR:-/tmp/ponderosa/surveys/pending}"
  PROCESSED_DIR="${PROCESSED_DIR:-/tmp/ponderosa/surveys/processed}"
  RECOMMENDER_PIPE="${RECOMMENDER_PIPE:-/tmp/ponderosa/pipes/recommender}"
  PRESENTER_PIPE="${PRESENTER_PIPE:-/tmp/ponderosa/pipes/presenter}"
else
  SURVEYS_DIR="${SURVEYS_DIR:-/var/ponderosa/surveys/pending}"
  PROCESSED_DIR="${PROCESSED_DIR:-/var/ponderosa/surveys/processed}"
  RECOMMENDER_PIPE="${RECOMMENDER_PIPE:-/var/ponderosa/pipes/recommender}"
  PRESENTER_PIPE="${PRESENTER_PIPE:-/var/ponderosa/pipes/presenter}"
fi
export SURVEYS_DIR PROCESSED_DIR RECOMMENDER_PIPE PRESENTER_PIPE

PYTHON="$(dirname "$0")/.venv/bin/python"
# Fall back to system python in dev (venv may not exist)
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi

exec "$PYTHON" main.py
