#!/usr/bin/env bash
# deploy.sh — one command to build and deploy everything
# Run from anywhere inside the cloud-systems repo:
#   bash ~/cloud-systems/final-project/deploy.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)/final-project"
ACR_NAME=jtrickeysdr bash build-push.sh
