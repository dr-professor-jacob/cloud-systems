#!/usr/bin/env bash
set -euo pipefail
START=$(date +%s)
cd ~/cloud-systems

echo "==> git pull"
git fetch origin
git reset --hard origin/master

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

# ── SSH source IP restriction ─────────────────────────────────────────────────
if [[ -z "${TF_VAR_allowed_ssh_ip:-}" ]]; then
  MY_IP=$(curl -sf https://api.ipify.org)
  export TF_VAR_allowed_ssh_ip="${MY_IP}/32"
  echo "==> SSH restricted to ${MY_IP}/32"
fi

# ── Cloudflare API token ──────────────────────────────────────────────────────
if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "==> CLOUDFLARE_API_TOKEN not set"
  read -rsp "    Enter Cloudflare API token: " CLOUDFLARE_API_TOKEN
  echo
  export CLOUDFLARE_API_TOKEN
fi

# ════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Main portfolio stack (root Tofu root)
# ════════════════════════════════════════════════════════════════════════════
echo ""
echo "==> [Phase 1] Main stack: tofu apply"
tofu apply -auto-approve

IP=$(tofu output -raw app_public_ip)
DOMAIN=$(tofu output -raw app_domain)
KV=$(tofu output -raw key_vault_name)
echo "==> App IP: $IP  Domain: $DOMAIN  KV: $KV"

# Keep inventory in sync with current public IP and Key Vault name
sed -i "s|jrick@[0-9.]*\"|jrick@${IP}\"|" inventory.ini
sed -i "s|^key_vault_name=.*|key_vault_name=${KV}|" inventory.ini

# ── Anthropic API key ─────────────────────────────────────────────────────────
if ! az keyvault secret show --vault-name "$KV" --name anthropic-api-key \
    --query value -o tsv &>/dev/null; then
  echo "==> anthropic-api-key not in Key Vault"
  read -rsp "    Enter Anthropic API key: " ANTHROPIC_KEY
  echo
  az keyvault secret set --vault-name "$KV" --name anthropic-api-key \
    --value "$ANTHROPIC_KEY" --output none
  echo "==> anthropic-api-key stored"
fi
ANTHROPIC_KEY=$(az keyvault secret show --vault-name "$KV" \
  --name anthropic-api-key --query value -o tsv)

# ── VM managed identity principal ID (used by RF project for role assignments) ─
VM_PRINCIPAL=$(az identity show \
  --name app-vm-identity \
  --resource-group cloud-v3 \
  --query principalId -o tsv 2>/dev/null || true)
echo "==> VM identity principal: ${VM_PRINCIPAL:-NOT FOUND}"

# ════════════════════════════════════════════════════════════════════════════
# PHASE 2 — RF Survey project (final-project/ Tofu root)
# ════════════════════════════════════════════════════════════════════════════
echo ""
echo "==> [Phase 2] RF Survey stack: final-project/"
cd ~/cloud-systems/final-project

# Get subscription ID from current az session
SUB_ID=$(az account show --query id -o tsv)

# Create project.auto.tfvars if it doesn't exist (only acr_name needs input)
if [[ ! -f project.auto.tfvars ]]; then
  echo "==> project.auto.tfvars not found"
  read -rp "    ACR name (globally unique, alphanumeric, 5-50 chars, e.g. jrickeysdr): " ACR_NAME_VAL
  cat > project.auto.tfvars <<EOF
subscription_id          = "${SUB_ID}"
location                 = "eastus"
resource_group_name      = "rf-survey-rg"
project_name             = "rfsrvy"
acr_name                 = "${ACR_NAME_VAL}"
anthropic_api_key        = "${ANTHROPIC_KEY}"
image_tag_worker         = "placeholder"
vm_identity_principal_id = "${VM_PRINCIPAL}"
EOF
  echo "==> project.auto.tfvars created"
else
  # Refresh computed values that may change between runs
  sed -i "s|^subscription_id\s*=.*|subscription_id          = \"${SUB_ID}\"|" project.auto.tfvars
  sed -i "s|^anthropic_api_key\s*=.*|anthropic_api_key        = \"${ANTHROPIC_KEY}\"|" project.auto.tfvars
  if [[ -n "$VM_PRINCIPAL" ]]; then
    sed -i "s|^vm_identity_principal_id\s*=.*|vm_identity_principal_id = \"${VM_PRINCIPAL}\"|" project.auto.tfvars
  fi
fi

[[ ! -d .terraform ]] && tofu init

echo "==> tofu apply (RF stack)"
tofu apply -auto-approve

# ── RF outputs → Key Vault ────────────────────────────────────────────────────
SB_FQN=$(tofu output -raw sb_namespace_fqn)
STORAGE_URL=$(tofu output -raw storage_account_url)
SB_PI_CONN=$(tofu output -raw sb_pi_connection_string)
ACR_SERVER=$(tofu output -raw acr_login_server)

echo "==> Storing RF secrets in Key Vault: $KV"
store_secret() {
  local name=$1 value=$2
  existing=$(az keyvault secret show --vault-name "$KV" --name "$name" \
    --query value -o tsv 2>/dev/null || true)
  if [[ "$existing" != "$value" ]]; then
    az keyvault secret set --vault-name "$KV" --name "$name" \
      --value "$value" --output none
    echo "    $name — updated"
  else
    echo "    $name — unchanged"
  fi
}
store_secret "rf-sb-namespace" "$SB_FQN"
store_secret "rf-storage-url"  "$STORAGE_URL"
store_secret "rf-sb-pi-conn"   "$SB_PI_CONN"

# ── Build and push worker image ───────────────────────────────────────────────
echo ""
echo "==> Building rf-worker image..."
ACR_NAME=$(echo "$ACR_SERVER" | cut -d. -f1)
export ACR_NAME
bash build-push.sh

# Back to repo root for ansible
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

echo "==> Running Ansible (site.yml + setup_app.yml includes rf-web)"
ansible-playbook site.yml -i inventory.ini

# ════════════════════════════════════════════════════════════════════════════
ELAPSED=$(( $(date +%s) - START ))
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Deploy complete  ($(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s)"
echo "════════════════════════════════════════════════════════════════"
echo "  Portfolio:  https://${DOMAIN}"
echo "  RF Survey:  https://rf.${DOMAIN}"
echo ""
echo "  Pi setup (SSH to sdr-node or use Pi Connect):"
echo "    RF_KEY_VAULT=${KV} sudo -E bash /path/to/pi/fetch_secrets.sh"
echo "    sudo systemctl start rf-ingest rf-dispatcher"
echo "════════════════════════════════════════════════════════════════"
