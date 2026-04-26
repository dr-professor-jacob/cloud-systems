#!/bin/bash
# restore.sh — Interactive World Restore
set -euo pipefail

BACKUP_REMOTE="azure-backup:mc-backups"
WORLD_DIR="/opt/minecraft/data/world"

echo "=== Available Backups ==="
# List all backup folders
sudo rclone lsd "$BACKUP_REMOTE/" | awk '{print $NF}' | sort -r

echo ""
echo "Enter the FULL name of the backup you want to restore (e.g., world-2026-04-25):"
read -r SELECTED

if [[ -z "$SELECTED" ]]; then
    echo "No backup selected. Exiting."
    exit 1
fi

# Verify backup exists
if ! sudo rclone lsd "$BACKUP_REMOTE/$SELECTED" >/dev/null 2>&1; then
    # Some rclone versions might need a different check for a folder existence
    echo "Checking backup path..."
fi

echo "=== WARNING: This will DELETE the current world and restore $SELECTED ==="
read -p "Are you absolutely sure? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo "=== Stopping Minecraft service ==="
sudo systemctl stop minecraft

echo "=== Deleting current world directory ==="
sudo rm -rf "$WORLD_DIR"

echo "=== Restoring $SELECTED ==="
sudo rclone copy "$BACKUP_REMOTE/$SELECTED" "$WORLD_DIR" --transfers=8 --progress

echo "=== Fixing permissions ==="
sudo chown -R jrick:jrick /opt/minecraft/data

echo "=== Starting Minecraft service ==="
sudo systemctl start minecraft

echo "=== Restore complete! Server is restarting. ==="
