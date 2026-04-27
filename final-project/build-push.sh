#!/usr/bin/env bash
# build-push.sh — build worker and web images, push to ACR, print deploy commands.
# Run from final-project/ directory in Azure Cloud Shell or locally with az login.
#
# Usage:
#   bash build-push.sh                  # auto-generates tag from git commit
#   TAG=v1.2 bash build-push.sh         # use explicit tag
set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────────────
ACR_NAME="${ACR_NAME:-}"         # override or set below
if [[ -z "$ACR_NAME" ]]; then
  ACR_NAME=$(tofu output -raw acr_login_server 2>/dev/null | cut -d. -f1 || true)
fi
if [[ -z "$ACR_NAME" ]]; then
  echo "ERROR: Set ACR_NAME env var or run 'tofu apply' first." >&2
  exit 1
fi

ACR="${ACR_NAME}.azurecr.io"

# Always pull latest before building so the tag matches what's in the repo
echo "==> Pulling latest from origin..."
git -C "$(git rev-parse --show-toplevel)" pull --ff-only

TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}"

echo "==> ACR:  $ACR"
echo "==> Tag:  $TAG"

# ── Build & push worker ───────────────────────────────────────────────────────
echo ""
echo "==> Building rf-worker..."
az acr build \
  --registry "$ACR_NAME" \
  --image "rf-worker:${TAG}" \
  --file worker/Dockerfile \
  worker/

# ── Deploy ────────────────────────────────────────────────────────────────────
# Note: rf-web runs on the portfolio VM (nginx proxy → port 8080).
# Only rf-worker lives in Container Apps.
echo ""
echo "==> Deploying rf-worker..."
az containerapp update --name rf-worker --resource-group rf-survey-rg \
  --image "${ACR}/rf-worker:${TAG}"

echo ""
echo "==> Deploying rf-web (via az vm run-command)..."
VM_RG="CLOUD-V3"
VM_NAME="app-vm"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
RAW="https://raw.githubusercontent.com/dr-professor-jacob/cloud-systems/${BRANCH}/final-project"
az vm run-command invoke \
  --resource-group "$VM_RG" --name "$VM_NAME" \
  --command-id RunShellScript \
  --scripts "
    curl -fsSL '${RAW}/web/main.py' -o /opt/rf-web/main.py
    curl -fsSL '${RAW}/web/static/waterfall.js' -o /opt/rf-web/static/waterfall.js
    curl -fsSL '${RAW}/web/templates/index.html' -o /opt/rf-web/templates/index.html
    sudo systemctl restart rf-web && echo 'rf-web restarted'
  " --query "value[0].message" -o tsv

echo ""
echo "==> Done. Tag: ${TAG}"
