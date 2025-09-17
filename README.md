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

# 3) Start Airflow (scheduler, API server, DAG processor)
make airflow-all

# 4) Add the Last.fm API key in Vault (dev)
Open http://localhost:8200 (token: dev-root)
Enable KV v2 at path "kv" → create secret kv/lastfm with key api_key=<YOUR_KEY>
```
# Live Connections
MinIO Console: [http://localhost:9001](http://localhost:9001) \
Vault UI: [http://localhost:8200](http://localhost:8200) \
pgAdmin: [http://localhost:5050](http://localhost:5050) \
airflow-api-server UI: [http://localhost:8080](https://localhost:8080)
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

## Airflow DAGs (ingestion)
Included DAGs

| DAG ID               | What it pulls                              | Schedule | Raw S3 prefix pattern                            |
| -------------------- | ------------------------------------------ | -------- | ------------------------------------------------ |
| `ingest_chart_daily` | `chart.getTopArtists/Tags/Tracks`          | `@daily` | `chart.getTop*/dt=YYYY-MM-DD/part-*.json`        |
| `ingest_geo_daily`   | `geo.getTopArtists/Tracks`                 | `@daily` | `geo.getTop*/dt=YYYY-MM-DD/part-*.json`          |
| `ingest_user_daily`  | `user.getRecentTracks` (default user `rj`) | `@daily` | `user.getRecentTracks/dt=YYYY-MM-DD/part-*.json` |

Extractors resolve the API key in this order: ENV `LASTFM_API_KEY` → Vault `kv/lastfm` key `api_key`.

### List dags
```bash
make airflow-dags
```

### Unpause and Trigger dags automaitically
```bash
make airflow-unpause
make airflow-trigger
```

### Trigger one-off runs
```bash
docker compose -f infra/compose.yaml exec -T airflow-api-server \
  airflow dags trigger ingest_chart_daily
docker compose -f infra/compose.yaml exec -T airflow-api-server \
  airflow dags trigger ingest_geo_daily
docker compose -f infra/compose.yaml exec -T airflow-api-server \
  airflow dags trigger ingest_user_daily
```
---

## Verifying things

### Verify Vault
```bash
docker compose -f infra/compose.yaml exec -T airflow-api-server sh -lc '
python - <<PY
import os, json, urllib.request
addr=os.getenv("VAULT_ADDR","http://127.0.0.1:8200")
tok=os.getenv("VAULT_TOKEN","dev-root")
req=urllib.request.Request(f"{addr}/v1/kv/data/lastfm", headers={"X-Vault-Token": tok})
print(json.dumps(json.load(urllib.request.urlopen(req))["data"]["data"], indent=2))
PY'

or you can do it siply by using make commands
make verify-vault
```
Expected output
`
{
  "api_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
`

To verify other objects inside containers, you can directly use help
from the make file using

`make help`

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
make help
  help                         Show this help message.
  check                        Validate docker compose config.
  ps                           List running services (all).
  logs                         Tail all logs.
  up                           Bring up core infra (postgres, minio, vault, pgadmin).
  core                         Start core services only.
  down                         Stop all containers (project-wide, no volume wipe).
  clean                        Stop and remove containers + volumes (DEV DATA LOSS).
  nuke                         Remove named volumes too (DEV ONLY).
  airflow-init                 Migrate Airflow DB & create admin user (one-shot).
  airflow-up                   Start Airflow API server + scheduler + DAG processor.
  airflow-stop                 Stop only Airflow containers (keep core running).
  airflow-restart              Restart Airflow services.
  airflow-dags                 List DAGs from inside API server.
  airflow-errors               Show DAG import errors.
  airflow-dagdir               Show DAGs folder inside container.
  airflow-unpause              Unpause the ingest_chart_daily DAG.
  airflow-trigger              Trigger the ingest_chart_daily DAG once.
  airflow-logs-dp              Tail DAG processor logs.
  get-airflow-password         Print generated Airflow login (simple_auth manager).
  airflow-smoke                Smoke-check S3 & Vault from inside Airflow (boto3 + curl).
  buckets                      Re-run MinIO bucket bootstrap script.
  verify-minio                 Ensure buckets exist (lists raw & curated).
  seed-buckets                 Force bucket creation script again.
  verify-pg                    Check DB created and raw.events table exists.
  seed-pg                      Re-run init SQL (schema/table bootstrap).
  verify-vault                 Read kv/lastfm from inside Airflow (container DNS).
  seed-vault                   Enable KV and write a demo LASTFM_API_KEY in dev Vault.
  fmt                          Run pre-commit on all files (format + lint).
  lint                         Alias for fmt (Black/isort/flake8 via pre-commit).
  test                         Install package in editable mode and run pytest fast-fail.
  verify                       Sanity-check core + app connectivity.
  core-up                      Start core & verify it is healthy.
  airflow-all                  Core + init + Airflow + smoke checks.
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

**No objects under prefixes even after triggering DAGs**
* Check Airflow task logs for `Missing LASTFM_API_KEY` or HTTP errors.
* Ensure `kv/lastfm` has `api_key` set, or export `LASTFM_API_KEY` into the container env.
* Confirm MinIO creds and `S3_ENDPOINT` are set in `infra/.env` and visible inside Airflow containers.

**`jq: not found` in containers**
* Use the Python verification snippets above (no `jq` required).

**MinIO “mc” job not running**
* That container may finish and exit after bootstrap; it’s expected. Use the Python S3 checks instead.

**Vault “kv” path mismatch**
* KV v2 read path is `/v1/<mount>/<path>`. With `VAULT_KV_MOUNT=kv`, the correct HTTP path is:
* GET `$VAULT_ADDR/v1/kv/lastfm` (header X-Vault-Token: $VAULT_TOKEN).

---

## Roadmap (brief)

* **Phase 2**: extractor modules and Airflow DAGs (`ingest_chart_daily`, `ingest_geo_daily`, …) writing partitions to MinIO.
* **Phase 3**: dbt models (silver/gold) + data tests.
* **Phase 4**: Superset dashboards.

---

## License

MIT
