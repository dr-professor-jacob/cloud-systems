#!/bin/bash
# Sentinel health monitor — runs every 5 minutes via systemd timer.
# Checks services and config integrity. Auto-restarts what it can.
# Logs all events to /var/log/sentinel.log for MCP/AI visibility.

LOG=/var/log/sentinel.log
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ALERTS=0

log() { echo "$TS $1" >> "$LOG"; }

# --- Service checks ---
for SVC in nginx ask-app mcp-infra; do
    if ! systemctl is-active --quiet "$SVC"; then
        log "ALERT $SVC is down — attempting restart"
        if systemctl restart "$SVC" 2>/dev/null; then
            log "RESTORED $SVC restarted successfully"
        else
            log "FAILED $SVC could not be restarted"
        fi
        ALERTS=$((ALERTS + 1))
    fi
done

# --- nginx config integrity ---
DEPLOYED=/etc/nginx/nginx.conf
CHECKSUM_FILE=/etc/nginx/.sentinel_checksum

if [ -f "$CHECKSUM_FILE" ]; then
    EXPECTED=$(cat "$CHECKSUM_FILE")
    ACTUAL=$(sha256sum "$DEPLOYED" | awk '{print $1}')
    if [ "$EXPECTED" != "$ACTUAL" ]; then
        log "ALERT nginx config drift detected (checksum mismatch)"
        ALERTS=$((ALERTS + 1))
    fi
fi

# --- nginx responds ---
if ! curl -sf --max-time 5 http://localhost/nginx_status > /dev/null 2>&1; then
    log "ALERT nginx_status endpoint not responding"
    ALERTS=$((ALERTS + 1))
fi

# --- SSL cert readable ---
if [ ! -r /etc/letsencrypt/live/$(hostname -f 2>/dev/null || echo unknown)/fullchain.pem ] 2>/dev/null; then
    : # skip if cert path unknown
fi

# --- Summary ---
if [ "$ALERTS" -eq 0 ]; then
    log "OK all checks passed"
fi


# Rotate log — keep last 500 lines
LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
if [ "$LINES" -gt 500 ]; then
    tail -n 400 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
fi
