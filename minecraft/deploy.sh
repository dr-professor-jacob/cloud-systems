#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
MY_IP=$(curl -sf https://checkip.amazonaws.com)/32
echo "=== terraform init ==="
terraform init
echo "=== terraform apply ==="
terraform apply -var "allowed_ssh_ip=${MY_IP}" "$@"
PUBLIC_IP=$(terraform output -raw public_ip)

echo "=== Pulling Anthropic key from Key Vault ==="
ANTHROPIC_KEY=$(az keyvault secret show \
  --vault-name cloud-v3-kv --name anthropic-api-key \
  --query value -o tsv)

echo "=== Waiting for SSH at ${PUBLIC_IP} ==="
until ssh -i ../cloud-systems \
    -o StrictHostKeyChecking=accept-new \
    -o ConnectTimeout=5 \
    jrick@"${PUBLIC_IP}" true 2>/dev/null; do
  echo "  waiting..."
  sleep 10
done

echo "=== Running Ansible ==="
cd ..
ansible-playbook -i minecraft/inventory.ini minecraft/setup_minecraft.yml \
  -e "anthropic_api_key=${ANTHROPIC_KEY}"

echo "Done. Connect: ${PUBLIC_IP}:25565"
