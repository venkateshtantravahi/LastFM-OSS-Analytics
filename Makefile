# -----------------------------
# LastFM OSS Analytics — Makefile
# -----------------------------

# Default goal prints help like real CLI tools
.DEFAULT_GOAL := help

# Paths / Compose wrapper
INFRA_DIR        := infra
DC               := cd $(INFRA_DIR) && docker compose -f compose.yaml --env-file .env

# Profiles
PROFILE_ENV      := COMPOSE_PROFILES=airflow

# Airflow Commons
AIRFLOW_API ?= airflow-api-server
AIRFLOW_SCHED ?= airflow-scheduler
AIRFLOW_DAGPROC ?= airflow-dag-processor

# Service groups
CORE_SERVICES    := postgres minio minio-mc vault pgadmin
AIRFLOW_SERVICES := airflow-api-server airflow-scheduler airflow-dag-processor
AIRFLOW_INIT     := airflow-init

# ------------- Helper: pretty help -------------
# Any target with a trailing '## comment' shows up in `make help`
help: ## Show this help message.
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ------------- Compose sanity ------------------
check: ## Validate docker compose config.
	@$(DC) config >/dev/null && echo "compose: OK"

ps: ## List running services (all).
	@$(DC) ps

logs: ## Tail all logs.
	@$(DC) logs -f --tail=200

logs-%: ## Tail logs for a specific service, e.g. make logs-airflow-api-server
	@$(DC) logs -f --tail=200 $*

restart-%: ## Recreate a single service in place, e.g. make restart-minio
	@$(DC) up -d --force-recreate $*

exec-%: ## Open a shell in a service, e.g. make exec-postgres
	@$(DC) exec $* sh -lc 'bash || sh'

# ------------- Core infra ----------------------
up: core ## Bring up core infra (postgres, minio, vault, pgadmin).
core: ## Start core services only.
	@$(DC) up -d $(CORE_SERVICES)

down: ## Stop all containers (project-wide, no volume wipe).
	@$(DC) down

clean: ## Stop and remove containers + volumes (DEV DATA LOSS).
	@$(DC) down -v

nuke: clean ## Remove named volumes too (DEV ONLY).
	-@docker volume rm lastfm_pgdata lastfm_minio lastfm_stack_airflow_logs 2>/dev/null || true

# ------------- Airflow lifecycle ----------------
airflow-init: core ## Migrate Airflow DB & create admin user (one-shot).
	@cd $(INFRA_DIR) && $(PROFILE_ENV) docker compose -f compose.yaml --env-file .env up $(AIRFLOW_INIT)

airflow-up: ## Start Airflow API server + scheduler + DAG processor.
	@cd $(INFRA_DIR) && $(PROFILE_ENV) docker compose -f compose.yaml --env-file .env up -d $(AIRFLOW_SERVICES)

airflow-stop: ## Stop only Airflow containers (keep core running).
	@$(DC) stop $(AIRFLOW_SERVICES)

airflow-down-clean: ## Stop Airflow and remove their volumes/logs (DEV DATA LOSS for Airflow only)
	@$(DC) down -v --remove-orphans $(AIRFLOW_SERVICES)

airflow-restart: ## Restart Airflow services.
	@$(MAKE) airflow-stop >/dev/null || true
	@$(MAKE) airflow-up

get-airflow-password: ## Print generated Airflow login (simple_auth manager).
	@cd $(INFRA_DIR) && docker compose --env-file .env exec airflow-api-server \
	bash -lc 'F="$${AIRFLOW_HOME:-/opt/airflow}/simple_auth_manager_passwords.json.generated"; \
	if [ -f "$$F" ]; then command -v jq >/dev/null 2>&1 && jq . "$$F" || cat "$$F"; \
	else echo "Password file not found. Start the Airflow API/Web once to generate it."; exit 1; fi'

airflow-smoke: ## Smoke-check S3 & Vault from inside Airflow (boto3 + curl).
	@$(DC) exec -T airflow-scheduler /bin/sh -lc '\
	  set -e; \
	  echo "S3_ENDPOINT=$$S3_ENDPOINT"; \
	  echo "VAULT_ADDR=$$VAULT_ADDR VAULT_TOKEN=$${VAULT_TOKEN:+set}"; \
	  curl -fsS "$$S3_ENDPOINT/minio/health/ready" >/dev/null && echo "minio: ok"; \
	  curl -fsS -H "X-Vault-Token: $$VAULT_TOKEN" "$$VAULT_ADDR/v1/sys/health" >/dev/null && echo "vault: ok"; \
	  python -c "import os, boto3; \
endpoint=os.environ.get(\"S3_ENDPOINT\"); \
ak=os.environ.get(\"MINIO_ROOT_USER\"); sk=os.environ.get(\"MINIO_ROOT_PASSWORD\"); \
s3=boto3.client(\"s3\", endpoint_url=endpoint, aws_access_key_id=ak, aws_secret_access_key=sk, region_name=\"us-east-1\"); \
print(\"buckets:\", [b[\"Name\"] for b in s3.list_buckets().get(\"Buckets\", [])])" \
	'

# ---- DB/metadata quick helpers (safe-ish) ----
airflow-refresh-dagbag: ## Force refresh of serialized DAGs (clears table).
	@$(DC) exec $(AIRFLOW_API) bash -lc "airflow dags reserialize"

airflow-db-check: ## Quick DB check (prints number of tables).
	@$(DC) exec $(AIRFLOW_API) bash -lc "airflow db check"

# --------------- Airflow DAGs lookups and testing locally ---------------------
# List / errors / where are my DAGs?

airflow-dags: ## List DAGs from inside API server.
	@$(DC) exec $(AIRFLOW_API) airflow dags list

airflow-errors: ## Show DAG import errors.
	@$(DC) exec $(AIRFLOW_API) airflow dags list-import-errors

airflow-dagdir: ## Show DAGs folder inside container.
	@$(DC) exec $(AIRFLOW_API) bash -lc 'echo "DAGS_FOLDER=${AIRFLOW__CORE__DAGS_FOLDER:-/opt/airflow/dags}"; ls -la ${AIRFLOW__CORE__DAGS_FOLDER:-/opt/airflow/dags}'

#--------Unpause / Trigger (single - DAG )----------
# Usage:
# make airflow-unpause DAG=ingest_chart_daily
# make airflow-trigger DAG=ingest_chart_daily
airflow-unpause: ## Unpause one DAG (DAG=<dag_id>)
	@test -n "$(DAG)" || (echo "DAG is required: make $@ DAG=<dag_id>"; exit 2)
	@$(DC) exec $(AIRFLOW_API) airflowdags unpause "$(DAG)"

airflow-trigger: ## Trigger one DAG once (DAG=<dag_id>)
	@test -n "$(DAG)" || (echo "DAG is required: make $@ DAG=<dag_id>"; exit 2)
	@$(DC) exec $(AIRFLOW_API) airflow dags trigger "$(DAG)"

# ---- Unpause / Trigger (many or all) ----
# Usage (many): make airflow-unpause-many DAGS="ingest_chart_daily ingest_geo_daily"
#               make airflow-trigger-many DAGS="ingest_chart_daily ingest_geo_daily"
airflow-unpause-many: ## Unpause many DAGs (DAGS="a b c")
	@test -n "$(DAGS)" || (echo "DAGS is required: make $@ DAGS=\"dag1 dag2 ...\""; exit 2)
	@$(DC) exec $(AIRFLOW_API) bash -lc 'for d in $(DAGS); do echo "unpause: $$d"; airflow dags unpause "$$d"; done'

airflow-trigger-many: ## Trigger many DAGs (DAGS="a b c")
	@test -n "$(DAGS)" || (echo "DAGS is required: make $@ DAGS=\"dag1 dag2 ...\""; exit 2)
	@$(DC) exec $(AIRFLOW_API) bash -lc 'for d in $(DAGS); do echo "trigger: $$d"; airflow dags trigger "$$d"; done'

airflow-unpause-all: ## Unpause all DAGs
	@$(DC) exec $(AIRFLOW_API) airflow dags unpause --treat-dag-id-as-regex '.*'

airflow-trigger-all: ## Trigger all DAGs
	@(DC) exec $(AIRFLOW_API) airflow dags trigger --treat-dag-id-as-regex '.*'

# ---- Health check: Scheduler -> API (v2 monitor endpoint) ----
airflow-api-health-check: ## check if scheduler is able to connect the api-server via health check
	@$(DC) exec -T $(AIRFLOW_SCHED) sh -lc '\
	echo "API URL: $$AIRFLOW__API__BASE_URL"; \
	curl -fsS "$$AIRFLOW__API__BASE_URL/api/v2/monitor/health" >/dev/null \
	&& echo "api: ok" || (echo "api: not ok" && exit 1)'

# ---- Logs while debugging ----
airflow-logs-api: ## Tail API server logs.
	@$(DC) logs -f --tail=200 $(AIRFLOW_API)

airflow-logs-scheduler: ## Tail Scheduler logs.
	@$(DC) logs -f --tail=200 $(AIRFLOW_SCHED)

airflow-logs-dp: ## Tail DAG Processor logs.
	@$(DC) logs -f --tail=200 $(AIRFLOW_DAGPROC)

# ---- Sanity check: ingested data in S3/MinIO ----
# Requires S3_ENDPOINT and S3_BUCKET_RAW available in the scheduler env.
airflow-check-ingested-data-head: ## Sanity check if data ingested properly into buckets
	@$(DC) exec -T $(AIRFLOW_SCHED) python /opt/airflow/scripts/check_s3.py

# ---- Local DAG testing / parsing / backfill ----
# Examples:
#   make airflow-parse DAG=ingest_chart_daily
#   make airflow-test DAG=ingest_chart_daily EXECUTION_DATE=2025-09-18
#   make airflow-backfill DAG=ingest_chart_daily START=2025-09-10 END=2025-09-12
airflow-parse: ## Parse a DAG to catch import/parse errors (DAG=<dag_id>)
	@test -n "$(DAG)" || (echo "DAG is required: make $@ DAG=<dag_id>"; exit 2)
	@$(DC) exec $(AIRFLOW_API) airflow dags parse "$(DAG)"

airflow-test: ## One-off test run (DAG=<dag_id> EXECUTION_DATE=<iso>)
	@test -n "$(DAG)" || (echo "DAG is required: make $@ DAG=<dag_id>"; exit 2)
	@test -n "$(EXECUTION_DATE)" || (echo "EXECUTION_DATE is required (e.g., 2025-09-18)"; exit 2)
	@$(DC) exec $(AIRFLOW_API) airflow dags test "$(DAG)" "$(EXECUTION_DATE)"

airflow-backfill: ## Backfill date range (DAG=<dag_id> START=<iso> END=<iso>)
	@test -n "$(DAG)" || (echo "DAG is required"; exit 2)
	@test -n "$(START)" || (echo "START is required (YYYY-MM-DD)"; exit 2)
	@test -n "$(END)" || (echo "END is required (YYYY-MM-DD)"; exit 2)
	@$(DC) exec $(AIRFLOW_API) airflow dags backfill -s "$(START)" -e "$(END)" "$(DAG)"


# ------------- MinIO buckets (idempotent) -------
buckets: ## Re-run MinIO bucket bootstrap script.
	@$(DC) up -d minio minio-mc
	@$(DC) exec minio-mc sh -lc '/usr/local/bin/create-buckets.sh || true'

verify-minio: ## Ensure buckets exist (lists raw & curated).
	@$(DC) run --rm minio_mc sh -lc '\
	  mc alias set local http://minio:9000 "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null; \
	  echo "raw:";     mc ls "local/$$S3_BUCKET_RAW" || true; \
	  echo "curated:"; mc ls "local/$$S3_BUCKET_CURATED" || true; \
	'
seed-buckets: ## Force bucket creation script again.
	@$(DC) exec -T minio-mc sh -lc '/usr/local/bin/create-buckets.sh'

# ------------- Postgres -------------------------
verify-pg: ## Check DB created and raw.events table exists.
	@$(DC) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -tAc "SELECT datname FROM pg_database WHERE datname='\''lastfm'\''" && psql -U "$$POSTGRES_USER" -d lastfm -tAc "SELECT to_regclass('\''raw.events'\'')"'

seed-pg: ## Re-run init SQL (schema/table bootstrap).
	@$(DC) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -f /docker-entrypoint-initdb.d/00_init.sql'

# ------------- Vault ----------------------------
verify-vault: ## Read kv/lastfm from inside Airflow (container DNS).
	@$(DC) exec -T airflow-api-server sh -lc '\
	  set -e; \
	  echo "VAULT_ADDR=$$VAULT_ADDR VAULT_TOKEN=$${VAULT_TOKEN:+set} VAULT_KV_MOUNT=$${VAULT_KV_MOUNT:-kv}"; \
	  mount=$${VAULT_KV_MOUNT:-kv}; \
	  if [ "$$mount" = "secret" ]; then path="/v1/$$mount/data/lastfm"; else path="/v1/$$mount/lastfm"; fi; \
	  curl -sf "$$VAULT_ADDR$$path" -H "X-Vault-Token: $$VAULT_TOKEN" \
	  | python -c "import sys,json; d=json.load(sys.stdin); x=d.get(\"data\",{}); x=x.get(\"data\",x); print(json.dumps(x,indent=2))" \
	  || echo "missing: $$mount/lastfm" \
	'
seed-vault: ## Enable KV and write a demo LASTFM_API_KEY in dev Vault.
	@$(DC) exec -T vault sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200; vault login "$$VAULT_DEV_ROOT_TOKEN_ID" >/dev/null; vault secrets enable -path=kv kv || true; vault kv put kv/lastfm api_key="$${LASTFM_API_KEY:-cf2de1533eae94e8d9ed49e220afbc14}"'

# ------------- Dev utilities --------------------
fmt: ## Run pre-commit on all files (format + lint).
	@pre-commit run -a

lint: fmt ## Alias for fmt (Black/isort/flake8 via pre-commit).

test: ## Install package in editable mode and run pytest fast-fail.
	@pip install -e .[dev] || pip install -e .
	@pytest -q --maxfail=1 --disable-warnings

# ------------- One-click flows ------------------
verify: verify-pg verify-vault verify-minio  ## Sanity-check core + app connectivity.

core-up: up verify ## Start core & verify it is healthy.

airflow-all: core airflow-init airflow-up airflow-smoke ## Core + init + Airflow + smoke checks.
