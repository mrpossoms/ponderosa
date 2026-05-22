#!/usr/bin/env bash
# Usage: ./run.sh [--dev]
#   PROCESSED_DIR  — source of completed surveys (default /var/ponderosa/surveys/processed)
#   SURVEYS_WEB    — web root for generated report pages (default /var/www/ponderosafireprotection.com/surveys)
#   PRESENTER_PIPE — named pipe written by recommender (default /var/ponderosa/pipes/presenter)
#   SURVEYS_URL    — public base URL for survey links in emails (default https://surveys.ponderosafireprotection.com)
#   SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / EMAIL_FROM — email config

set -e

cd "$(dirname "$0")"

if [[ "$1" == "--dev" ]]; then
  PROCESSED_DIR="${PROCESSED_DIR:-/tmp/ponderosa/surveys/processed}"
  SURVEYS_WEB="${SURVEYS_WEB:-/tmp/ponderosa/surveys/web}"
  PRESENTER_PIPE="${PRESENTER_PIPE:-/tmp/ponderosa/pipes/presenter}"
  SURVEYS_URL="${SURVEYS_URL:-http://localhost:8080}"
else
  PROCESSED_DIR="${PROCESSED_DIR:-/var/ponderosa/surveys/processed}"
  SURVEYS_WEB="${SURVEYS_WEB:-/var/www/ponderosafireprotection.com/surveys}"
  PRESENTER_PIPE="${PRESENTER_PIPE:-/var/ponderosa/pipes/presenter}"
  SURVEYS_URL="${SURVEYS_URL:-https://surveys.ponderosafireprotection.com}"
fi
export PROCESSED_DIR SURVEYS_WEB PRESENTER_PIPE SURVEYS_URL

PYTHON="$(dirname "$0")/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi

exec "$PYTHON" main.py
