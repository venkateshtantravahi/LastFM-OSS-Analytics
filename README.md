# LastFM OSS Analytics

Open‑source, local‑first data platform that ingests public Last.fm data, stores raw JSON in S3‑compatible object storage (MinIO), optionally mirrors into Postgres for inspection, and prepares analytics for dashboards. No cloud lock‑in.

---

## Architecture (high‑level)

```
Last.fm API  →  Ingestion (Python)  →  MinIO (raw/bronze)
                                    →  Postgres (raw.events) [optional]

Later phases:
MinIO/PG → dbt (silver/gold) → Superset (dashboards)
Airflow orchestrates scheduled ingestion jobs
Vault manages secrets (dev mode locally)
```

---

## Prerequisites

* Git ≥ 2.40
* Docker Desktop (or Colima/OrbStack) with Compose v2
* Python 3.11+
* make (GNU Make)

> Works on macOS/Linux/WSL2. Windows users should prefer WSL2.

---

## Quickstart (5 minutes)

```bash
# 1) Configure environment
cp infra/.env.template infra/.env

# 2) Start services (Postgres, MinIO, Vault, pgAdmin)
make up

# 3) Add the Last.fm API key in Vault (dev)
# Open http://localhost:8200 (token: dev-root)
# Enable KV v2 at path "kv" → create secret kv/lastfm with key api_key=<YOUR_KEY>
```

MinIO Console: [http://localhost:9001](http://localhost:9001)
Vault UI: [http://localhost:8200](http://localhost:8200)
pgAdmin: [http://localhost:5050](http://localhost:5050)

---

## Running a smoke test (manual)

This confirms API access and object storage writes.

```python
# Run inside a virtualenv, after `pip install -e .` from the repo root
from src.ingestion.lastfm_client import LastFM
import os, json, uuid, datetime as dt
import boto3, requests

# 1) Resolve API key (Vault → env fallback)
api = os.getenv("LASTFM_API_KEY")
if not api:
    VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    TOKEN = os.getenv("VAULT_TOKEN", "dev-root")
    r = requests.get(f"{VAULT_ADDR}/v1/kv/data/lastfm", headers={"X-Vault-Token": TOKEN}, timeout=5).json()
    api = r["data"]["data"]["api_key"]

client = LastFM(api_key=api)
tracks = client.recent_tracks(user="rj", limit=5)

# 2) Write to MinIO (S3‑compatible)
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "admin"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "adminadmin"),
    region_name=os.getenv("S3_REGION", "us-east-1"),
)

bucket = os.getenv("S3_BUCKET_RAW", "lastfm-raw")
key = f"user.getRecentTracks/dt={dt.date.today():%Y-%m-%d}/part-{uuid.uuid4()}.json"
s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(tracks).encode("utf-8"))
print("wrote:", bucket, key)
```

You should see the object under the bucket in MinIO Console.

---

## Configuration

All runtime settings live in `infra/.env` (copied from `.env.template`). Key variables:

**Postgres**

```
PGUSER, PGPASSWORD, PGDATABASE, PGHOST, PGPORT
```

**MinIO / S3**

```
MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
S3_ENDPOINT, S3_REGION, S3_BUCKET_RAW, S3_BUCKET_CURATED
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
```

**Vault (dev)**

```
VAULT_ADDR=http://127.0.0.1:8200
VAULT_DEV_ROOT_TOKEN_ID=dev-root
```

> Secrets are stored in Vault (dev mode). Never commit real tokens to git.

---

## Repository layout

```
lastfm-oss-analytics/
├─ infra/                    # docker compose + .env
├─ docker/
│  ├─ minio/create-buckets.sh   # idempotent bucket bootstrap
│  └─ vault/
│     ├─ policies/*.hcl         # sample policies for non-dev mode
│     └─ config.hcl             # sample server config (not used in dev mode)
├─ src/
│  └─ ingestion/
│     ├─ lastfm_client.py       # minimal API client
│     └─ jobs/                  # to be filled with endpoint extractors
├─ tests/
│  └─ test_ci.py                # minimal CI smoke test
├─ .github/workflows/ci.yml     # lint + tests on PRs
├─ .pre-commit-config.yaml
├─ pyproject.toml
├─ Makefile
└─ README.md
```

---

## Make commands

```makefile
make up        # start containers
make down      # stop and remove containers + volumes (dev only)
make logs      # follow compose logs
make fmt       # run pre-commit hooks (black/isort/flake8)
make test      # run pytest
```

---

## CI

GitHub Actions installs the package and runs formatting + tests.

* If you see CI fail due to "no tests collected", ensure `tests/test_ci.py` exists with:

  ```python
  def test_ci_is_alive():
      assert True
  ```
* To include dev tools via pip extras, add to `pyproject.toml`:

  ```toml
  [project.optional-dependencies]
  dev = ["pytest>=8", "pre-commit>=3.7"]
  ```

  Then in CI: `pip install -e .[dev]`.

---

## Troubleshooting

**Vault port in use / listener error**

* In dev we run `vault server -dev`. Do **not** mount `config.hcl` at `/vault/config` simultaneously this creates a second listener and causes `address already in use`.
* Optionally set `VAULT_API_ADDR=http://vault:8200` to quiet warnings.

**MinIO not ready for mc**

* The `minio-mc` job waits and retries. If you see an early `connection refused` but buckets are created afterward, it’s fine.
* You can rerun the script: `docker compose -f infra/compose.yaml exec minio-mc sh -lc '/usr/local/bin/create-buckets.sh'`.

**Postgres init SQL didn’t run**

* Ensure the volume target is `/docker-entrypoint-initdb.d`.
* If the DB already initialized without it, run the SQL manually or `make down` (dev only) then `make up`.

---

## Roadmap (brief)

* **Phase 2**: add extractor modules and Airflow DAGs (`ingest_chart_daily`, `ingest_geo_daily`, …) writing partitions to MinIO.
* **Phase 3**: dbt models (silver/gold) + data tests.
* **Phase 4**: Superset dashboards.

---

## License

MIT
