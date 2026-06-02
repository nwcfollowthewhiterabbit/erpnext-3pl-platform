#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo ".env is missing; copy .env.example and fill secrets" >&2
  exit 1
fi

set -a
. ./.env
set +a

stack_name="${STACK_NAME:?set STACK_NAME}"
site_name="${SITE_NAME:?set SITE_NAME}"
erpnext_image="${ERPNEXT_IMAGE:?set ERPNEXT_IMAGE}"
public_url="${1:-http://127.0.0.1:${FRONTEND_PORT:-8080}}"

wait_for_replicas() {
  timeout_seconds="$1"
  start_ts="$(date +%s)"

  while true; do
    docker stack services "$stack_name"
    bad_replicas="$(
      docker stack services "$stack_name" --format "{{.Name}} {{.Replicas}}" |
        awk '
          $1 ~ /_(configurator|create-site)$/ { next }
          $2 != "1/1" { print }
        '
    )"

    if [ -z "$bad_replicas" ]; then
      return 0
    fi

    if [ "$(( $(date +%s) - start_ts ))" -ge "$timeout_seconds" ]; then
      echo "$bad_replicas" >&2
      echo "Timed out waiting for stack replicas" >&2
      return 1
    fi

    sleep 10
  done
}

get_backend_cid() {
  docker ps --filter "label=com.docker.swarm.service.name=${stack_name}_backend" -q | head -1
}

wait_for_backend_exec() {
  timeout_seconds="$1"
  start_ts="$(date +%s)"

  while true; do
    backend_cid="$(get_backend_cid)"
    if [ -n "$backend_cid" ] && docker exec "$backend_cid" true >/dev/null 2>&1; then
      printf "%s" "$backend_cid"
      return 0
    fi

    if [ "$(( $(date +%s) - start_ts ))" -ge "$timeout_seconds" ]; then
      echo "Timed out waiting for a running backend container" >&2
      return 1
    fi

    sleep 5
  done
}

backend_cid="$(get_backend_cid)"
if [ -z "$backend_cid" ]; then
  echo "Backend container for ${stack_name}_backend is not running" >&2
  exit 1
fi

echo "Creating ERPNext backup for ${site_name}"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} backup --with-files"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ls -1t sites/${site_name}/private/backups | head -5"

echo "Pulling ${erpnext_image}"
docker pull "$erpnext_image"

echo "Deploying ${stack_name} with ${erpnext_image}"
docker stack deploy -c compose.yml "$stack_name"
wait_for_replicas 900

backend_cid="$(wait_for_backend_exec 180)"

docker cp scripts/run_project_script.py "$backend_cid":/tmp/run_project_script.py
docker cp scripts/prepare_major_upgrade.py "$backend_cid":/tmp/prepare_major_upgrade.py

echo "Running pre-migration cleanup for ${site_name}"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ./env/bin/python /tmp/run_project_script.py ${site_name} /tmp/prepare_major_upgrade.py 1"

echo "Running bench migrate for ${site_name}"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} migrate"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} clear-cache"

./scripts/run_post_deploy.sh
./scripts/validate_instance.sh "$public_url"

echo "Existing instance deploy complete for ${site_name} using ${erpnext_image}"
