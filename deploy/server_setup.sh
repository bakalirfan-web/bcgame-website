#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/myserver/DATA/bcgame/TGbot/newbot"
SERVICE_NAME="tgbot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cd "${APP_DIR}"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

sudo cp deploy/tgbot.service "${SERVICE_FILE}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl restart "${SERVICE_NAME}.service"

sudo systemctl --no-pager --full status "${SERVICE_NAME}.service" || true
echo "Deployment complete."
