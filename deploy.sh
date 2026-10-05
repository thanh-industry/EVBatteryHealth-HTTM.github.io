#!/usr/bin/env bash
# Redeploy the EV Battery SoH app to the production server.
#
# Builds the frontend locally and ships it with the backend, so the server
# does not need Node installed. Credentials are NEVER stored here: set
# DEPLOY_HOST and authenticate with an SSH key or ssh-agent.
#
#   DEPLOY_HOST=root@139.59.245.176 ./deploy.sh
#
set -euo pipefail

HOST="${DEPLOY_HOST:?set DEPLOY_HOST, e.g. root@139.59.245.176}"
APP_DIR=/opt/evsoh
WEB_DIR=/var/www/evsoh

echo "==> Building frontend"
( cd frontend && npm ci && npm run build )

echo "==> Packaging"
TMP=$(mktemp -d)
tar -czf "$TMP/evsoh.tar.gz" \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' \
  --exclude='backend/data' --exclude='backend/.venv' \
  backend/app backend/tests backend/requirements.txt backend/pytest.ini \
  "ev battery_failure prediction Dataset.csv" \
  -C frontend dist

echo "==> Uploading"
scp "$TMP/evsoh.tar.gz" "$HOST:$APP_DIR/evsoh.tar.gz"
rm -rf "$TMP"

echo "==> Installing on server"
ssh "$HOST" bash -s <<REMOTE
set -euo pipefail
cd $APP_DIR
rm -rf backend/app backend/tests dist
tar -xzf evsoh.tar.gz && rm evsoh.tar.gz
rm -rf $WEB_DIR/* && mv dist/* $WEB_DIR/ && rmdir dist
chown -R evsoh:evsoh $APP_DIR
chown -R www-data:www-data $WEB_DIR
backend/.venv/bin/pip install -q -r backend/requirements.txt
systemctl restart evsoh-api
sleep 4
systemctl is-active evsoh-api
curl -fsS http://127.0.0.1:8000/api/config/thresholds && echo " <- backend OK"
REMOTE

echo "==> Verifying public endpoint"
curl -fsS https://evsoh.thingiq.ai/api/config/thresholds && echo " <- live OK"
echo "Done: https://evsoh.thingiq.ai"
