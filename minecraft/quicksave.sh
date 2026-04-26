#!/bin/bash
# quicksave.sh — Runs every 30 mins if players are online.
set -euo pipefail

BACKUP_REMOTE="azure-backup:mc-backups/quicksaves"
WORLD_DIR="/opt/minecraft/data/world"
RCON="sudo docker exec minecraft rcon-cli"

# 1. Check if players are online
PLAYER_COUNT=$($RCON list | grep -oP '\d+(?= of a max)')

if [ "$PLAYER_COUNT" -eq 0 ]; then
    echo "$(date): No players online. Skipping quicksave."
    exit 0
fi

echo "=== Player(s) detected ($PLAYER_COUNT). Starting quicksave... ==="

# 2. Sync to Azure with timestamp
TS=$(date +%Y-%m-%d-%H%M)
$RCON save-all
sleep 2

sudo rclone sync "$WORLD_DIR" "$BACKUP_REMOTE/quick-$TS" --transfers=8

# 3. Cleanup: Keep only last 12 quicksaves (6 hours of play)
echo "--- Cleaning old quicksaves ---"
sudo rclone lsd "azure-backup:mc-backups/quicksaves/" | awk '{print $NF}' | sort | head -n -12 | xargs -r -I{} sudo rclone purge "azure-backup:mc-backups/quicksaves/{}"

echo "=== Quicksave complete: quick-$TS ==="
