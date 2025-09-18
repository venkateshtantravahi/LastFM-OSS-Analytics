import os

import requests

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
TOKEN = os.getenv("VAULT_TOKEN", "dev-root")
resp = requests.get(
    f"{VAULT_ADDR}/v1/kv/lastfm", headers={"X-Vault-Token": TOKEN}
).json()

# get api_key
api_key = resp["data"]["data"]["api_key"]
# get secret
api_secret = resp["data"]["data"]["api_secret"]

print(api_key)
print(api_secret)
