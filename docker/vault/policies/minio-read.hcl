# read only access to last.fm api key at kv/lastfm

path "data/kv/lastfm" {
  capabilities = ["read"]
}
