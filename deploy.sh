#!/usr/bin/env bash
IP=$(terraform output -raw app_public_ip)
DOMAIN="${IP}.nip.io"
python3 -c "print(open('templates/index.html.j2').read().replace('{{ app_domain }}','${DOMAIN}'))" > /tmp/index.html
az vm run-command invoke -g cloud-v3 -n app-vm --command-id RunShellScript --scripts "cat > /var/www/html/index.html << 'HTMLEOF'
$(cat /tmp/index.html)
HTMLEOF"
echo "Done: https://${DOMAIN}"
