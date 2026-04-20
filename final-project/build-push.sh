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
echo "==> Deploying rf-web..."
REPO_ROOT="$(git rev-parse --show-toplevel)"
ansible-playbook -i "${REPO_ROOT}/inventory.ini" "${REPO_ROOT}/setup_app.yml"

echo ""
echo "==> Done. Tag: ${TAG}"
