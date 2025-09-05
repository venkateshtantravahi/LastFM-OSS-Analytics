# read only access to postgres dsn kept at kv/postgres
path "data/kv/postgres" {
  capabilities = ["read"]
}
