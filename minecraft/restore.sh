#!/bin/bash
# restore.sh — Restores the latest world backup from Azure Blob.
set -euo pipefail

BACKUP_REMOTE="azure-backup:mc-backups"
WORLD_DIR="/opt/minecraft/data/world"

echo "=== Listing available backups ==="
BACKUPS=$(sudo rclone lsd "$BACKUP_REMOTE/" | awk '{print $NF}' | sort -r)

if [[ -z "$BACKUPS" ]]; then
    echo "No backups found in $BACKUP_REMOTE"
    exit 1
fi

LATEST=$(echo "$BACKUPS" | head -n 1)
echo "Latest backup found: $LATEST"

read -p "Restore this backup? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo "=== Stopping Minecraft service ==="
sudo systemctl stop minecraft

echo "=== Deleting current world directory ==="
sudo rm -rf "$WORLD_DIR"

echo "=== Restoring $LATEST ==="
sudo rclone copy "$BACKUP_REMOTE/$LATEST" "$WORLD_DIR" --transfers=8 --progress

echo "=== Fixing permissions ==="
sudo chown -R jrick:jrick /opt/minecraft/data

echo "=== Starting Minecraft service ==="
sudo systemctl start minecraft

echo "=== Restore complete! ==="
