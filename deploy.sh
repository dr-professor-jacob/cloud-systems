#!/usr/bin/env bash
set -e

echo "==> terraform apply"
terraform apply -auto-approve

IP=$(terraform output -raw app_public_ip)
echo "==> App IP: $IP"

echo "==> Waiting for SSH on $IP..."
until ssh -i mits_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 jrick@"$IP" true 2>/dev/null; do
  echo "    not ready, retrying in 5s..."
  sleep 5
done
echo "==> SSH ready"

echo "==> Running app playbook"
ansible-playbook setup_app.yml -i inventory.ini

echo "==> Running db playbook"
ansible-playbook setup_db.yml -i inventory.ini

echo "==> Done: https://${IP}.nip.io"
