#!/usr/bin/env bash
# Deploy the EV Battery Failure Classification app to the production server.
#
# Credentials are NEVER stored here: set DEPLOY_HOST and authenticate with an
# SSH key or ssh-agent.
#
#   DEPLOY_HOST=root@your.server ./deploy.sh
#
# What this ships and what it deliberately does not:
#
#   ships   app/ deployment/ ml_pipeline/ (source only)
#   leaves  models/  - the deployed model bundle lives on the server
#           data/    - the application database lives on the server
#
# Overwriting either of those from a developer machine is how production state
# gets lost, so they are excluded rather than merely "usually skipped".
#
set -euo pipefail

HOST="${DEPLOY_HOST:?set DEPLOY_HOST, e.g. root@198.51.100.10}"
APP_DIR="${DEPLOY_APP_DIR:-/opt/evsoh-app}"
SERVICE="${DEPLOY_SERVICE:-evsoh-app}"
VENV="$APP_DIR/.venv"

echo "==> Packaging source"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
tar -czf "$TMP/release.tar.gz" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='.ipynb_checkpoints' \
  --exclude='ml_pipeline/artifacts' \
  app deployment ml_pipeline

echo "==> Uploading"
scp -q "$TMP/release.tar.gz" "$HOST:/tmp/release.tar.gz"

echo "==> Installing"
ssh "$HOST" APP_DIR="$APP_DIR" SERVICE="$SERVICE" VENV="$VENV" bash -s <<'REMOTE'
set -euo pipefail

# Back up the database before touching anything. Cheap, and the one thing
# that cannot be rebuilt from the repository.
if [ -f "$APP_DIR/data/app.db" ]; then
  cp "$APP_DIR/data/app.db" "$APP_DIR/data/app.db.$(date +%Y%m%d-%H%M%S).bak"
fi

cd "$APP_DIR"
rm -rf app deployment ml_pipeline
tar -xzf /tmp/release.tar.gz
rm -f /tmp/release.tar.gz

"$VENV/bin/pip" install -q -r app/requirements.txt

# Run the suite ON THE SERVER. This project has twice been bitten by library
# drift between the developer machine and the server (a Streamlit API change
# and a scikit-learn pickle mismatch), both of which passed locally.
"$VENV/bin/python" -m pytest app/tests -q

chown -R evsoh:evsoh "$APP_DIR"
systemctl restart "$SERVICE"
sleep 5
systemctl is-active --quiet "$SERVICE" || {
  echo "service failed to start:"
  journalctl -u "$SERVICE" --since '1 min ago' --no-pager | tail -30
  exit 1
}
echo "service active"
REMOTE

echo "==> Deployed"
