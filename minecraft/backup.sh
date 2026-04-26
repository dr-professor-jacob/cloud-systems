#!/bin/bash
# Daily world backup to Azure Blob via rclone.
# Pauses world saving during transfer to avoid chunk corruption.
set -euo pipefail

WORLD_DIR=/opt/minecraft/data/world
BACKUP_REMOTE="azure-backup:mc-backups"
DATE=$(date +%Y-%m-%d)
LOG=/var/log/mc-backup.log

exec >> "$LOG" 2>&1
echo "=== Backup started: $(date) ==="

docker exec minecraft rcon-cli save-all
docker exec minecraft rcon-cli save-off
sleep 5

rclone sync "$WORLD_DIR" "$BACKUP_REMOTE/world-$DATE" \
  --transfers=4 \
  --log-level INFO

# Keep only the last 7 daily snapshots
rclone lsd "$BACKUP_REMOTE/" \
  | awk '{print $NF}' \
  | sort \
  | head -n -7 \
  | xargs -r -I{} rclone purge "$BACKUP_REMOTE/{}"

docker exec minecraft rcon-cli save-on
echo "=== Backup complete: $(date) ==="
