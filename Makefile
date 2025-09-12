#-----------Config-------------
COMPOSE := docker compose -f compose.yaml --env-file .env
PROFILE_ENV := COMPOSE_PROFILES=airflow

SERVICES_CORE := postgres minio minio-mc vault pgadmin
SERVICES_AIRFLOW := airflow-api-server airflow-scheduler
AIRFLOW_INIT := airflow-init

#---------- Phony----------
.PHONY: help check \
		up core ps logs logs-% restart-% exec-% \
		airflow-init airflow-up airflow-all airflow-down \
		buckets down clean nuke fmt lint test \
		verify verify-pg verify-minio verify-vault seed-pg \
		seed-buckets seed-vault get-airflow-password

#------------Help---------------
help:
	@echo "make up            # bring up core infra (postgres, minio, vault, pgadmin)"
	@echo "make airflow-init  # migrate Airflow DB + create admin user (one-shot)"
	@echo "make airflow-up    # start Airflow webserver + scheduler"
	@echo "make airflow-all   # core + init + airflow"
	@echo "make down          # stop all containers (no volume wipe)"
	@echo "make clean         # stop + remove volumes (dev data loss)"
	@echo "make nuke          # clean + remove named docker volumes"
	@echo "make ps            # list services"
	@echo "make logs          # tail all logs"
	@echo "make logs-<svc>    # tail logs for a service (e.g., logs-airflow-webserver)"
	@echo "make restart-<svc> # force-recreate one service"
	@echo "make exec-<svc>    # shell into a service"
	@echo "make buckets       # re-run MinIO bucket bootstrap"
	@echo "make fmt|lint|test # dev utilities (pre-commit / pytest)"
	@echo "make verify 		  #sanity check on core containers"
	@echo "make verify-pg     #check to verify if postgres running and schemas got created"
	@echo "make verify-minio  #sanity check on minio container"
	@echo "make verify-vault  #sanity check on vault services"
	@echo "make seed-pg 	  #re-running init script to initialize objects"
	@echo "make seed-buckets  #re initializing buckets"
	@echo "make seed-vault    #re initializing vault with secrets and reading policies"
	@echo "get-airflow-password #get the generated passcode."
#----------- Compose Sanity ---------------------------
check:
	cd infra && $(COMPOSE) config >/dev/null && echo "compose ok".


# ------------ Core Infra ---------------------
up: core
core:
	cd infra && $(COMPOSE) up -d $(SERVICES_CORE)

ps:
	cd infra && $(COMPOSE) ps

logs:
	cd infra && $(COMPOSE) logs -f --tail=200

logs-%:
	cd infra && $(COMPOSE) logs -f --tail=200 $*

restart-%:
	cd infra && $(COMPOSE) up -d --force-recreate $*

exec-%:
	cd infra && $(COMPOSE) exec $* sh -lc 'bash || sh'


# --------------- Airflow ------------------------
airflow-init: core
	cd infra && $(PROFILE_ENV) $(COMPOSE) up $(AIRFLOW_INIT)

airflow-up:
	cd infra && $(PROFILE_ENV) $(COMPOSE) up -d $(SERVICES_AIRFLOW)

airflow-all: core airflow-init airflow-up

airflow-down:
	cd infra && $(PROFILE_ENV) $(COMPOSE) down

get-airflow-password:
	cd infra && docker compose --env-file .env exec airflow-api-server \
	bash -lc 'FILE="$${AIRFLOW_HOME:-/opt/airflow}/simple_auth_manager_passwords.json.generated"; \
		if [ -f "$$FILE" ]; then \
		  if command -v jq >/dev/null 2>&1; then jq . "$$FILE"; else cat "$$FILE"; fi; \
		else \
		  echo "Password file not found. Start the Airflow web/API service once to generate it."; \
		  exit 1; \
		fi'

# ---------- MINIO buckets (idempotent) -----------

buckets:
	cd infra && $(COMPOSE) exec minio-mc sh -lc '/usr/local/bin/create-buckets.sh || true'

# --------- Verifying ----------------------
verify: verify-pg verify-minio verify-vault

verify-pg:
	cd infra && $(COMPOSE) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -tAc "SELECT datname FROM pg_database WHERE datname='\''lastfm'\''" && psql -U "$$POSTGRES_USER" -d lastfm -tAc "SELECT to_regclass('\''raw.events'\'')"'

seed-pg:
	cd infra && $(COMPOSE) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -f /docker-entrypoint-initdb.d/00_init.sql'

verify-minio:
	cd infra && $(COMPOSE) exec -T minio-mc sh -lc 'mc alias set local http://minio:9000 "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null 2>&1 || true; mc ls "local/$$S3_BUCKET_RAW" && mc ls "local/$$S3_BUCKET_CURATED"'

seed-buckets:
	cd infra && $(COMPOSE) exec -T minio-mc sh -lc '/usr/local/bin/create-buckets.sh'

verify-vault:
	curl -sf "$$VAULT_ADDR/v1/kv/data/lastfm" -H "X-Vault-Token: $$VAULT_DEV_ROOT_TOKEN_ID" | jq '.data.data' || echo "kv/lastfm missing"

seed-vault:
	cd infra && $(COMPOSE) exec -T vault sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200; vault login "$$VAULT_DEV_ROOT_TOKEN_ID"; vault secrets enable -path=kv kv || true; vault kv put kv/lastfm api_key="${LASTFM_API_KEY:-cf2de1533eae94e8d9ed49e220afbc14}"'

# ---------- Teardown ----------
down:
	cd infra && $(COMPOSE) down

clean:
	cd infra && $(COMPOSE) down -v

# Remove named volumes too (dev only)
nuke: clean
	-docker volume rm lastfm_pgdata lastfm_minio airflow_logs

# ---------- Dev ----------
fmt:
	pre-commit run -a

lint: fmt

test:
	pip install -e .[dev] || pip install -e .
	pytest -q --maxfail=1 --disable-warnings
