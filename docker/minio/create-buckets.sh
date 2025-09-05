#!/usr/bin/env bash
set -euo pipefail

#Defaults (override via env)
: "${MINIO_ROOT_USER:?MINIO_ROOT_USER not set}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD not set}"
: "${S3_BUCKET_RAW:=lastfm-raw}"
: "${S3_BUCKET_CURATED:=lastfm-curated}"

#Configure alias and create buckets idempotently
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# wait until response back
until mc ls local >/dev/null 2>&1; do
  echo "[create-buckets] waiting for MINIO..."
  sleep 2
  mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" || true
done

echo "[create-buckets] Creating buckets: $S3_BUCKET_RAW, $S3_BUCKET_CURATED"
mc mb -p "local/${S3_BUCKET_RAW}" || true
mc mb -p "local/${S3_BUCKET_CURATED}" || true

mc anonymous set download "local/${S3_BUCKET_CURATED}" || true

echo "[create-buckets] Done."
