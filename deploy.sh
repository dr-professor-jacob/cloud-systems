#!/usr/bin/env bash
set -euo pipefail
START=$(date +%s)
cd ~/cloud-systems

echo "==> git sync"
git stash -q 2>/dev/null || true
git fetch origin
git checkout -B master origin/master

# ── OpenTofu installation ─────────────────────────────────────────────────────
if ! command -v tofu &>/dev/null; then
  echo "==> Installing OpenTofu to ~/bin..."
  mkdir -p "$HOME/bin"
  TOFU_VER="1.9.0"
  curl -fsSL "https://github.com/opentofu/opentofu/releases/download/v${TOFU_VER}/tofu_${TOFU_VER}_linux_amd64.zip" \
    -o /tmp/tofu.zip
  unzip -q /tmp/tofu.zip -d /tmp/tofu-extract
  mv /tmp/tofu-extract/tofu "$HOME/bin/tofu"
  chmod +x "$HOME/bin/tofu"
  export PATH="$HOME/bin:$PATH"
fi

# ── Key Vault is the single source of truth for all secrets/config ────────────
# KV name is a constant — it's hardcoded in main.tf and created by Phase 1.
# On first-ever run KV may not exist yet; kv_get_or_prompt handles that by
# prompting and storing silently (no-op if KV absent, retried after Phase 1).
KV="cloud-v3-kv"

kv_get_or_prompt() {
  # Usage: kv_get_or_prompt <secret-name> <prompt-text> [silent]
  local name=$1 prompt=$2 silent=${3:-false}
  local val
  val=$(az keyvault secret show --vault-name "$KV" --name "$name" \
    --query value -o tsv 2>/dev/null || true)
  if [[ -z "$val" ]]; then
    echo "==> $name not in Key Vault — enter once, stored for all future runs" >&2
    if [[ "$silent" == "true" ]]; then
      read -rsp "    $prompt: " val; echo >&2
    else
      read -rp  "    $prompt: " val
    fi
    # Store now if KV already exists; silently skip if not (retried after Phase 1)
    az keyvault secret set --vault-name "$KV" --name "$name" \
      --value "$val" --output none 2>/dev/null || true
  fi
  printf '%s' "$val"
}

store_kv() {
  local name=$1 value=$2
  local existing
  existing=$(az keyvault secret show --vault-name "$KV" --name "$name" \
    --query value -o tsv 2>/dev/null || true)
  if [[ "$existing" != "$value" ]]; then
    az keyvault secret set --vault-name "$KV" --name "$name" \
      --value "$value" --output none
    echo "    $name — stored"
  fi
}

# ── Load all config/secrets from KV (prompt once if missing) ─────────────────
echo "==> Loading config from Key Vault..."
CF_TOKEN=$(kv_get_or_prompt "cloudflare-api-token" "Cloudflare API token" "true")
CF_ZONE=$(kv_get_or_prompt  "cloudflare-zone-id"   "Cloudflare Zone ID (Cloudflare dashboard → domain → Overview → right sidebar)")
DOMAIN=$(kv_get_or_prompt   "domain-name"          "Domain name (e.g. jrickey.cc)")
ANTHROPIC_KEY=$(kv_get_or_prompt "anthropic-api-key" "Anthropic API key" "true")

export CLOUDFLARE_API_TOKEN="$CF_TOKEN"

# ── SSH source IP restriction ─────────────────────────────────────────────────
if [[ -z "${TF_VAR_allowed_ssh_ip:-}" ]]; then
  MY_IP=$(curl -sf https://api.ipify.org)
  export TF_VAR_allowed_ssh_ip="${MY_IP}/32"
  echo "==> SSH restricted to ${MY_IP}/32"
fi

# ════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Main portfolio stack (root Tofu root)
# ════════════════════════════════════════════════════════════════════════════
echo ""
echo "==> [Phase 1] Main stack: tofu apply"
tofu apply -auto-approve \
  -var "cloudflare_zone_id=${CF_ZONE}" \
  -var "domain_name=${DOMAIN}"

IP=$(tofu output -raw app_public_ip)
DOMAIN_OUT=$(tofu output -raw app_domain)
echo "==> App IP: $IP  Domain: $DOMAIN_OUT  KV: $KV"

sed -i "s|jrick@[0-9.]*\"|jrick@${IP}\"|" inventory.ini
sed -i "s|^key_vault_name=.*|key_vault_name=${KV}|" inventory.ini

# KV now definitely exists — store anything that failed earlier
echo "==> Syncing secrets to Key Vault..."
store_kv "cloudflare-api-token" "$CF_TOKEN"
store_kv "cloudflare-zone-id"   "$CF_ZONE"
store_kv "domain-name"          "$DOMAIN"
store_kv "anthropic-api-key"    "$ANTHROPIC_KEY"

# ── VM managed identity principal ID ─────────────────────────────────────────
VM_PRINCIPAL=$(az identity show \
  --name app-vm-identity --resource-group cloud-v3 \
  --query principalId -o tsv 2>/dev/null || true)
echo "==> VM identity principal: ${VM_PRINCIPAL:-NOT FOUND}"

# ════════════════════════════════════════════════════════════════════════════
# PHASE 2 — RF Survey project (final-project/ Tofu root)
# ════════════════════════════════════════════════════════════════════════════
echo ""
echo "==> [Phase 2] RF Survey stack: final-project/"
cd ~/cloud-systems/final-project

SUB_ID=$(az account show --query id -o tsv)

# Find existing Container App Environment (student sub: 1 per region)
CAE_NAME=$(az containerapp env list --subscription "$SUB_ID" \
  --query "[0].name" -o tsv 2>/dev/null || true)
CAE_RG=$(az containerapp env list --subscription "$SUB_ID" \
  --query "[0].resourceGroup" -o tsv 2>/dev/null || true)
echo "==> Container App Environment: ${CAE_NAME:-NONE} (rg: ${CAE_RG:-?})"

# ACR name stored in KV — prompt once
ACR_NAME_VAL=$(kv_get_or_prompt "acr-name" "ACR name (globally unique, alphanumeric, e.g. jrickeysdr)")
store_kv "acr-name" "$ACR_NAME_VAL"

# Always regenerate project.auto.tfvars from KV — no stale state
cat > project.auto.tfvars <<EOF
subscription_id          = "${SUB_ID}"
location                 = "eastus"
resource_group_name      = "rf-survey-rg"
project_name             = "rfsrvy"
acr_name                 = "${ACR_NAME_VAL}"
anthropic_api_key        = "${ANTHROPIC_KEY}"
image_tag_worker         = "placeholder"
vm_identity_principal_id = "${VM_PRINCIPAL}"
container_app_env_name   = "${CAE_NAME}"
container_app_env_rg     = "${CAE_RG}"
EOF

[[ ! -d .terraform ]] && tofu init

echo "==> tofu apply (RF stack)"
tofu apply -auto-approve

# ── RF outputs → Key Vault ────────────────────────────────────────────────────
SB_FQN=$(tofu output -raw sb_namespace_fqn)
STORAGE_URL=$(tofu output -raw storage_account_url)
SB_PI_CONN=$(tofu output -raw sb_pi_connection_string)
ACR_SERVER=$(tofu output -raw acr_login_server)

echo "==> Storing RF outputs in Key Vault..."
store_kv "rf-sb-namespace" "$SB_FQN"
store_kv "rf-storage-url"  "$STORAGE_URL"
store_kv "rf-sb-pi-conn"   "$SB_PI_CONN"

# ── Build and push worker image ───────────────────────────────────────────────
echo ""
echo "==> Building rf-worker image..."
export ACR_NAME
ACR_NAME=$(echo "$ACR_SERVER" | cut -d. -f1)
bash build-push.sh

cd ~/cloud-systems

# ════════════════════════════════════════════════════════════════════════════
# PHASE 3 — VM provisioning (Ansible)
# ════════════════════════════════════════════════════════════════════════════
echo ""
echo "==> [Phase 3] Waiting for SSH on $IP..."
until ssh -i cloud-systems \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=5 \
    jrick@"$IP" true 2>/dev/null; do
  echo "    not ready, retrying in 5s..."
  sleep 5
done
echo "==> SSH ready"

ssh-keygen -R "$IP" 2>/dev/null || true
ssh-keygen -R 10.0.1.4 2>/dev/null || true
ssh-keyscan -H "$IP" >> ~/.ssh/known_hosts
ssh-keyscan -H 10.0.1.4 >> ~/.ssh/known_hosts

echo "==> Running Ansible..."
ansible-playbook site.yml -i inventory.ini

# ════════════════════════════════════════════════════════════════════════════
ELAPSED=$(( $(date +%s) - START ))
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Deploy complete  ($(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s)"
echo "════════════════════════════════════════════════════════════════"
echo "  Portfolio:  https://${DOMAIN_OUT}"
echo "  RF Survey:  https://rf.${DOMAIN_OUT}"
echo ""
echo "  Pi setup (via Pi Connect or SSH to sdr-node):"
echo "    RF_KEY_VAULT=${KV} sudo -E bash pi/fetch_secrets.sh"
echo "    sudo systemctl start rf-ingest rf-dispatcher"
echo "════════════════════════════════════════════════════════════════"
