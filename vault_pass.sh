#!/usr/bin/env bash
# Fetches the Ansible Vault password from Azure Key Vault at runtime.
# Requires az CLI authenticated (automatic in Azure Cloud Shell).
az keyvault secret show \
  --vault-name cloud-v3-kv \
  --name ansible-vault-pass \
  --query value \
  --output tsv 2>/dev/null
