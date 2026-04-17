#!/usr/bin/env bash
# fetch_secrets.sh — runs at boot via fetch-secrets.service
# Uses the VM's managed identity (IMDS) to pull secrets from Key Vault.
# Writes to /run/ (tmpfs) — never touches persistent disk.
set -e

VAULT="cloud-v3-kv"
API="7.3"

# Get an access token for Key Vault from the Instance Metadata Service
TOKEN=$(curl -sf \
  -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token\
?api-version=2018-02-01&resource=https%3A%2F%2Fvault.azure.net" \
  | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['access_token'])")

get_secret() {
  curl -sf \
    -H "Authorization: Bearer $TOKEN" \
    "https://${VAULT}.vault.azure.net/secrets/$1?api-version=${API}" \
    | python3 -c \
    "import sys,json; print(json.load(sys.stdin)['value'])"
}

# Optional — returns empty string instead of aborting if secret not found yet
get_secret_opt() {
  get_secret "$1" 2>/dev/null || true
}

mkdir -p /run/secrets

# ── ask-app env (ANTHROPIC_API_KEY) ────────────────────────────────────────
ANTHROPIC_KEY=$(get_secret anthropic-api-key)
printf 'ANTHROPIC_API_KEY=%s\n' "$ANTHROPIC_KEY" > /run/secrets/ask-app.env
chmod 600 /run/secrets/ask-app.env

# ── nginx MCP auth map (mcp-api-key) ───────────────────────────────────────
MCP_KEY=$(get_secret mcp-api-key)
mkdir -p /run/nginx
{
  printf 'map $http_authorization $mcp_auth_ok {\n'
  printf '    "Bearer %s" 1;\n' "$MCP_KEY"
  printf '    default 0;\n'
  printf '}\n'
} > /run/nginx/mcp_auth.conf
chmod 640 /run/nginx/mcp_auth.conf
chown root:www-data /run/nginx/mcp_auth.conf

# ── rf-web env — optional until RF project tofu apply has run ─────────────
RF_SB=$(get_secret_opt rf-sb-namespace)
RF_STORAGE=$(get_secret_opt rf-storage-url)
if [[ -n "$RF_SB" && -n "$RF_STORAGE" ]]; then
  {
    printf 'SERVICE_BUS_NAMESPACE=%s\n' "$RF_SB"
    printf 'STORAGE_ACCOUNT_URL=%s\n'   "$RF_STORAGE"
    printf 'ANTHROPIC_API_KEY=%s\n'     "$ANTHROPIC_KEY"
  } > /run/secrets/rf.env
  chmod 600 /run/secrets/rf.env
else
  echo "fetch_secrets: rf KV secrets not present yet — rf.env skipped" >&2
fi
