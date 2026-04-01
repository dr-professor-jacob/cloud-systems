#!/usr/bin/env bash
# build-push.sh
# Builds the subnets-fork image, tags it with a semantic version, and pushes
# both the versioned tag and the latest alias to ACR.
#
# Prerequisites:
#   - az login completed
#   - tofu apply has been run (ACR must exist)
#
# Usage:
#   bash build-push.sh 1.0.0
#   bash build-push.sh 1.1.0

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: bash build-push.sh <version>"
    echo "Example: bash build-push.sh 1.0.0"
    exit 1
fi

VERSION="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

ACR=$(tofu -chdir="$SCRIPT_DIR" output -raw acr_login_server)
APP="subnets"
SRC="$HOME/Cloud/subnets-fork"

echo ""
echo "ACR:     $ACR"
echo "Image:   $ACR/$APP:$VERSION"
echo "Source:  $SRC"
echo ""

az acr login --name "${ACR%%.*}"

docker build "$SRC" -t "$ACR/$APP:$VERSION"
docker tag "$ACR/$APP:$VERSION" "$ACR/$APP:latest"

docker push "$ACR/$APP:$VERSION"
docker push "$ACR/$APP:latest"

echo ""
echo "Pushed: $ACR/$APP:$VERSION"
echo "Pushed: $ACR/$APP:latest"
echo ""
echo "Next step:"
echo "  tofu -chdir=$SCRIPT_DIR apply -var image_tag=$VERSION"
