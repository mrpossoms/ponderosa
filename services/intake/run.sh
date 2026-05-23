#!/usr/bin/env bash
# Usage: ./run.sh [--dev]
#   SURVEYS_DIR      — where survey subdirs are written (default /var/ponderosa/surveys/pending)
#   SESSIONS_DIR     — where session tokens are stored (default /var/ponderosa/sessions)
#   RECOMMENDER_PIPE — path to the named pipe (default /var/ponderosa/pipes/recommender)
#   APP_URL          — base URL for magic links (default https://app.ponderosafireprotection.com)
#   SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / EMAIL_FROM — email config

set -e

cd "$(dirname "$0")"

if [[ "$1" == "--dev" ]]; then
  SURVEYS_DIR="${SURVEYS_DIR:-/tmp/ponderosa/surveys/pending}"
  SESSIONS_DIR="${SESSIONS_DIR:-/tmp/ponderosa/sessions}"
  RECOMMENDER_PIPE="${RECOMMENDER_PIPE:-/tmp/ponderosa/pipes/recommender}"
  APP_URL="${APP_URL:-http://localhost:8080/app.html}"
  DEV=1
  export DEV
else
  SURVEYS_DIR="${SURVEYS_DIR:-/var/ponderosa/surveys/pending}"
  SESSIONS_DIR="${SESSIONS_DIR:-/var/ponderosa/sessions}"
  RECOMMENDER_PIPE="${RECOMMENDER_PIPE:-/var/ponderosa/pipes/recommender}"
  APP_URL="${APP_URL:-https://app.ponderosafireprotection.com}"
fi
export SURVEYS_DIR SESSIONS_DIR RECOMMENDER_PIPE APP_URL

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
