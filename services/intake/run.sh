#!/usr/bin/env bash
# Usage: ./run.sh [--dev]
#   SURVEYS_DIR      — where survey subdirs are written (default /var/ponderosa/surveys/pending)
#   RECOMMENDER_PIPE — path to the named pipe (default /var/ponderosa/pipes/recommender)

set -e

cd "$(dirname "$0")"

if [[ "$1" == "--dev" ]]; then
  SURVEYS_DIR="${SURVEYS_DIR:-/tmp/ponderosa/surveys/pending}"
  RECOMMENDER_PIPE="${RECOMMENDER_PIPE:-/tmp/ponderosa/pipes/recommender}"
  DEV=1
  export DEV
else
  SURVEYS_DIR="${SURVEYS_DIR:-/var/ponderosa/surveys/pending}"
  RECOMMENDER_PIPE="${RECOMMENDER_PIPE:-/var/ponderosa/pipes/recommender}"
fi
export SURVEYS_DIR RECOMMENDER_PIPE

mkdir -p "$SURVEYS_DIR"
mkdir -p "$(dirname "$RECOMMENDER_PIPE")"

PID_FILE=/tmp/ponderosa.intake.pid

UVICORN="$(dirname "$0")/.venv/bin/uvicorn"
# Fall back to system uvicorn in dev (venv may not exist)
if [[ ! -x "$UVICORN" ]]; then UVICORN=uvicorn; fi

if [[ "$1" == "--dev" ]]; then
  "$UVICORN" main:app --reload --host 0.0.0.0 --port 8001 &
else
  "$UVICORN" main:app --host 0.0.0.0 --port 8001 --workers 2 &
fi

echo $! > "$PID_FILE"
wait
