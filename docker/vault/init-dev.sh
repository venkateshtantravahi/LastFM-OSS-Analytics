#!/usr/bin/env bash
set -euo pipefail

export VAULT_ADDR=${VAULT_ADDR:-http://127.0.0.1:8200}
VAULT_TOKEN=${VAULT_TOKEN:-dev-root}

vault login "$VAULT_TOKEN"
# enable KVv2 at path=kv (idempotent)
vault secrets enable -path=kv kv || true

#create example secrets if not present
vault kv put kv/lastfm api_key="${LASTFM_API_KEY:-cf2de1533eae94e8d9ed49e220afbc14}"
vault kv put kv/postgres url="${POSTGRES_URL:-postgresql://postgres:PostGresUser@postgres:5432/lastfm}"

# Load example policies
vault policy write minio-read /vault/policies/minio-read.hcl
vault policy write postgres-read /vault/policies/postgres-read.hcl


echo "[vault-init] KV, secrets, and policies are ready."
