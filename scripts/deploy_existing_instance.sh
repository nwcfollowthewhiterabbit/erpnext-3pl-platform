#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

env_file="${PROJECT_ENV_FILE:-.env}"
if [ ! -f "$env_file" ]; then
  echo "$env_file is missing; copy .env.example and fill secrets" >&2
  exit 1
fi

set -a
. "$env_file"
set +a

stack_name="${STACK_NAME:?set STACK_NAME}"
site_name="${SITE_NAME:?set SITE_NAME}"
erpnext_image="${ERPNEXT_IMAGE:?set ERPNEXT_IMAGE}"
public_url="${1:-http://127.0.0.1:${FRONTEND_PORT:-8080}}"
project_env=(
  -e "WAREHOUSE_OPERATOR_PASSWORD=${WAREHOUSE_OPERATOR_PASSWORD:?set WAREHOUSE_OPERATOR_PASSWORD}"
  -e "WAREHOUSE_MANAGER_PASSWORD=${WAREHOUSE_MANAGER_PASSWORD:?set WAREHOUSE_MANAGER_PASSWORD}"
  -e "BUSINESS_OWNER_USER=${BUSINESS_OWNER_USER:?set BUSINESS_OWNER_USER}"
  -e "BUSINESS_OWNER_PASSWORD=${BUSINESS_OWNER_PASSWORD:?set BUSINESS_OWNER_PASSWORD}"
  -e "CLIENT_DESK_PASSWORD=${CLIENT_DESK_PASSWORD:?set CLIENT_DESK_PASSWORD}"
)

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
  stable_seconds="${2:-10}"

  while true; do
    backend_cid="$(get_backend_cid)"
    if [ -n "$backend_cid" ] && docker exec "$backend_cid" true >/dev/null 2>&1; then
      sleep "$stable_seconds"
      if [ "$backend_cid" = "$(get_backend_cid)" ] && docker exec "$backend_cid" true >/dev/null 2>&1; then
        printf "%s" "$backend_cid"
        return 0
      fi
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

if [ "${DEPLOY_BUILD_IMAGE:-0}" = "1" ]; then
  ./scripts/build_app_image.sh
else
  echo "Pulling ${erpnext_image}"
  docker pull "$erpnext_image"
fi

echo "Deploying ${stack_name} with ${erpnext_image}"
docker stack deploy -c compose.yml "$stack_name"
if [ "${DEPLOY_BUILD_IMAGE:-0}" = "1" ] && [ "${DEPLOY_PUSH_IMAGE:-0}" != "1" ]; then
  for service in backend frontend queue-long queue-short scheduler websocket; do
    docker service update --force "${stack_name}_${service}" >/dev/null
  done
fi
wait_for_replicas 900

backend_cid="$(wait_for_backend_exec 240 10)"

echo "Running pre-migration cleanup for ${site_name}"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} execute erpnext_3pl.maintenance.prepare_major_upgrade.main"

if docker exec "$backend_cid" bash -lc "test -d /home/frappe/frappe-bench/apps/erpnext_3pl"; then
  if docker exec "$backend_cid" bash -lc "cd /home/frappe/frappe-bench && bench --site ${site_name} list-apps | awk '{print \$1}' | grep -qx erpnext_3pl"; then
    echo "ERPNext 3PL app is already installed on ${site_name}"
  else
    echo "Installing ERPNext 3PL app on ${site_name}"
    docker exec "${project_env[@]}" "$backend_cid" bash -lc \
      "cd /home/frappe/frappe-bench && bench --site ${site_name} install-app erpnext_3pl"
  fi
fi

echo "Running bench migrate for ${site_name}"
docker exec "${project_env[@]}" "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} migrate"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} clear-cache"

./scripts/run_post_deploy.sh
./scripts/validate_instance.sh "$public_url"

echo "Existing instance deploy complete for ${site_name} using ${erpnext_image}"
