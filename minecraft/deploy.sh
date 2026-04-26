#!/bin/bash
# Bootstrap: apply OpenTofu, then run Ansible.
set -euo pipefail

cd "$(dirname "$0")"

MY_IP=$(curl -sf https://checkip.amazonaws.com)/32

echo "=== tofu init ==="
tofu init

echo "=== tofu apply ==="
tofu apply -var "allowed_ssh_ip=${MY_IP}" "$@"

PUBLIC_IP=$(tofu output -raw public_ip)
echo "=== Instance ready at ${PUBLIC_IP} — waiting for SSH ==="
until ssh -i ./mc-server -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
    ubuntu@"${PUBLIC_IP}" true 2>/dev/null; do
  echo "  waiting..."
  sleep 10
done

echo "=== Running Ansible ==="
cd ..
ansible-playbook -i minecraft/inventory.ini minecraft/setup_minecraft.yml

echo ""
echo "Done. Connect: ${PUBLIC_IP}:25565"
echo "SSH: ssh -i minecraft/mc-server ubuntu@${PUBLIC_IP}"
