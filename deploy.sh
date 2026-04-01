#!/usr/bin/env bash
set -e
START=$(date +%s)
cd ~/cloud-systems

echo "==> git pull"
git pull

# ── OpenTofu installation ─────────────────────────────────────────────────────
if ! command -v tofu &> /dev/null; then
    echo "==> OpenTofu not found, installing..."
    sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
    curl -fsSL https://get.opentofu.org/opentofu.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/opentofu.gpg
    sudo chmod a+r /etc/apt/keyrings/opentofu.gpg
    echo \
      "deb [signed-by=/etc/apt/keyrings/opentofu.gpg] https://packages.opentofu.org/opentofu/tofu/any/ \
      any main" | sudo tee /etc/apt/sources.list.d/opentofu.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y tofu
    echo "==> OpenTofu installed successfully."
fi


# ── SSH source IP restriction ─────────────────────────────────────────────────
if [ -z "$TF_VAR_allowed_ssh_ip" ]; then
  MY_IP=$(curl -sf https://api.ipify.org)
  export TF_VAR_allowed_ssh_ip="${MY_IP}/32"
  echo "==> SSH restricted to ${MY_IP}/32"
fi

# ── Cloudflare API token ──────────────────────────────────────────────────────
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "==> CLOUDFLARE_API_TOKEN not set"
  read -rs -p "    Enter Cloudflare API token: " CLOUDFLARE_API_TOKEN
  echo
  export CLOUDFLARE_API_TOKEN
fi

echo "==> tofu apply"
tofu apply -auto-approve

IP=$(tofu output -raw app_public_ip)
DOMAIN=$(tofu output -raw app_domain)
KV=$(tofu output -raw key_vault_name)
echo "==> App IP: $IP  Domain: $DOMAIN"

# Keep inventory in sync with current public IP and Key Vault name
sed -i "s|jrick@[0-9.]*\"|jrick@${IP}\"|" inventory.ini
sed -i "s|^key_vault_name=.*|key_vault_name=${KV}|" inventory.ini

# ── Anthropic API key ─────────────────────────────────────────────────────────
if ! az keyvault secret show \
    --vault-name "$KV" \
    --name anthropic-api-key \
    --query value -o tsv &>/dev/null; then
  echo "==> anthropic-api-key not in Key Vault"
  read -rs -p "    Enter Anthropic API key: " ANTHROPIC_KEY
  echo
  az keyvault secret set \
    --vault-name "$KV" \
    --name anthropic-api-key \
    --value "$ANTHROPIC_KEY" \
    --output none
  echo "==> anthropic-api-key stored"
fi

echo "==> Waiting for SSH on $IP..."
until ssh -i mits_key \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=5 \
    jrick@"$IP" true 2>/dev/null; do
  echo "    not ready, retrying in 5s..."
  sleep 5
done
echo "==> SSH ready"

echo "==> Running Ansible playbooks"
ansible-playbook site.yml -i inventory.ini

ELAPSED=$(( $(date +%s) - START ))
MINS=$(( ELAPSED / 60 ))
SECS=$(( ELAPSED % 60 ))
echo "==> Done: https://${DOMAIN}  (${MINS}m ${SECS}s)"
