#!/usr/bin/env bash
# fetch_secrets.sh — run at Pi boot to pull secrets from Key Vault.
# Prerequisites: `az login` done once on this device (token persists ~90 days).
#
# Usage: RF_KEY_VAULT=cloud-v3-kv sudo -E bash fetch_secrets.sh
set -e

VAULT="${RF_KEY_VAULT:-cloud-v3-kv}"

echo "==> Fetching secrets from Key Vault: $VAULT"

kv_get() {
  az keyvault secret show --vault-name "$VAULT" --name "$1" --query value -o tsv 2>/dev/null || true
}

SB_CONN=$(kv_get "rf-sb-pi-conn")
STORAGE_URL=$(kv_get "rf-storage-url")
STORAGE_CONN=$(kv_get "rf-storage-conn")

if [[ -z "$SB_CONN" ]]; then
  echo "ERROR: rf-sb-pi-conn not found in Key Vault $VAULT" >&2
  exit 1
fi

mkdir -p /run/secrets
{
  printf 'SERVICE_BUS_CONNECTION_STRING=%s\n' "$SB_CONN"
  [[ -n "$STORAGE_URL"  ]] && printf 'STORAGE_ACCOUNT_URL=%s\n'          "$STORAGE_URL"
  [[ -n "$STORAGE_CONN" ]] && printf 'AZURE_STORAGE_CONNECTION_STRING=%s\n' "$STORAGE_CONN"
} > /run/secrets/rf.env
chmod 600 /run/secrets/rf.env

# Also persist to /etc/rf/rf.env so it survives reboots (rf-secrets.service copies this)
mkdir -p /etc/rf
cp /run/secrets/rf.env /etc/rf/rf.env
chmod 600 /etc/rf/rf.env

echo "==> Secrets written to /run/secrets/rf.env and /etc/rf/rf.env"
echo "    Keys set: SERVICE_BUS_CONNECTION_STRING$([ -n "$STORAGE_URL" ] && echo ", STORAGE_ACCOUNT_URL")$([ -n "$STORAGE_CONN" ] && echo ", AZURE_STORAGE_CONNECTION_STRING")"
