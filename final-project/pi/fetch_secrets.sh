#!/usr/bin/env bash
# fetch_secrets.sh — run at Pi boot to pull Service Bus connection string from Key Vault.
# Prerequisites: `az login` done once on this device (token persists ~90 days).
#
# Usage: sudo bash fetch_secrets.sh
set -e

VAULT="${RF_KEY_VAULT:-rf-survey-kv}"   # override with: RF_KEY_VAULT=myname-kv bash fetch_secrets.sh

echo "==> Fetching secrets from Key Vault: $VAULT"

SB_CONN=$(az keyvault secret show \
  --vault-name "$VAULT" \
  --name "service-bus-conn-string" \
  --query value -o tsv)

mkdir -p /run/secrets
printf 'SERVICE_BUS_CONNECTION_STRING=%s\n' "$SB_CONN" > /run/secrets/rf.env
chmod 600 /run/secrets/rf.env

echo "==> Secrets written to /run/secrets/rf.env"

# ---------------------------------------------------------------------------
# Fallback: if Key Vault is not yet set up, create rf.env manually:
#   sudo mkdir -p /run/secrets
#   sudo bash -c 'echo "SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://..." > /run/secrets/rf.env'
#   sudo chmod 600 /run/secrets/rf.env
#
# Get the connection string from Cloud Shell:
#   tofu output -raw sb_pi_connection_string
# ---------------------------------------------------------------------------
