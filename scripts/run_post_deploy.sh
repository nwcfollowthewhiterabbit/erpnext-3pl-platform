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

site_name="${SITE_NAME:?set SITE_NAME}"
stack_name="${STACK_NAME:?set STACK_NAME}"

backend_service="${stack_name}_backend"
backend_cid="$(docker ps --filter "label=com.docker.swarm.service.name=${backend_service}" -q | head -1)"

if [ -z "$backend_cid" ]; then
  echo "Backend container for ${backend_service} is not running" >&2
  exit 1
fi

project_env=(
  -e "WAREHOUSE_OPERATOR_PASSWORD=${WAREHOUSE_OPERATOR_PASSWORD:?set WAREHOUSE_OPERATOR_PASSWORD}"
  -e "WAREHOUSE_MANAGER_PASSWORD=${WAREHOUSE_MANAGER_PASSWORD:?set WAREHOUSE_MANAGER_PASSWORD}"
  -e "BUSINESS_OWNER_USER=${BUSINESS_OWNER_USER:?set BUSINESS_OWNER_USER}"
  -e "BUSINESS_OWNER_PASSWORD=${BUSINESS_OWNER_PASSWORD:?set BUSINESS_OWNER_PASSWORD}"
  -e "CLIENT_DESK_PASSWORD=${CLIENT_DESK_PASSWORD:?set CLIENT_DESK_PASSWORD}"
)

docker exec -u root "$backend_cid" bash -lc \
  "mkdir -p /home/frappe/logs /home/frappe/frappe-bench/sites/${site_name}/logs && chown -R frappe:frappe /home/frappe/logs /home/frappe/frappe-bench/sites/${site_name}/logs"

app_installed=0
if docker exec "$backend_cid" bash -lc "cd /home/frappe/frappe-bench && bench --site ${site_name} list-apps | awk '{print \$1}' | grep -qx erpnext_3pl"; then
  app_installed=1
fi

if [ "$app_installed" != "1" ]; then
  echo "ERPNext 3PL app is not installed on ${site_name}" >&2
  exit 1
fi

if [ "${RUN_SITE_BOOTSTRAP:-0}" = "1" ]; then
  docker exec "${project_env[@]}" "$backend_cid" bash -lc \
    "cd /home/frappe/frappe-bench && bench --site ${site_name} execute erpnext_3pl.bootstrap.site.main"
fi

if [ "${RUN_DEMO_DATA:-0}" = "1" ]; then
  docker exec "${project_env[@]}" "$backend_cid" bash -lc \
    "cd /home/frappe/frappe-bench && bench --site ${site_name} execute erpnext_3pl.demo.users.main"
  docker exec "${project_env[@]}" "$backend_cid" bash -lc \
    "cd /home/frappe/frappe-bench && bench --site ${site_name} execute erpnext_3pl.demo.warehouse_data.main"
fi

if [ "${RUN_RECOVERY_PROCESSORS:-0}" = "1" ]; then
  for method in \
    erpnext_3pl.warehouse.container_moves.main \
    erpnext_3pl.warehouse.container_repacks.main \
    erpnext_3pl.warehouse.warehouse_corrections.main \
    erpnext_3pl.sync.receiving_notices.main \
    erpnext_3pl.sync.client_products.main \
    erpnext_3pl.sync.inventory_snapshots.main \
    erpnext_3pl.sync.inventory_balance_snapshots.main \
    erpnext_3pl.sync.shipment_requests.main \
    erpnext_3pl.sync.picking_confirmations.main \
    erpnext_3pl.sync.outbound_fulfillment.main \
    erpnext_3pl.sync.inventory_snapshots.main \
    erpnext_3pl.sync.inventory_balance_snapshots.main
  do
    docker exec "${project_env[@]}" "$backend_cid" bash -lc \
      "cd /home/frappe/frappe-bench && bench --site ${site_name} execute ${method}"
  done
fi

docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} clear-cache"

echo "Post-deploy maintenance complete for ${site_name}"
