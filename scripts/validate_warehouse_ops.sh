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
warehouse_operator_password="${WAREHOUSE_OPERATOR_PASSWORD:?set WAREHOUSE_OPERATOR_PASSWORD}"
warehouse_manager_password="${WAREHOUSE_MANAGER_PASSWORD:?set WAREHOUSE_MANAGER_PASSWORD}"
business_owner_user="${BUSINESS_OWNER_USER:?set BUSINESS_OWNER_USER}"
business_owner_password="${BUSINESS_OWNER_PASSWORD:?set BUSINESS_OWNER_PASSWORD}"
client_desk_password="${CLIENT_DESK_PASSWORD:?set CLIENT_DESK_PASSWORD}"

backend_cid="$(docker ps --filter "label=com.docker.swarm.service.name=${stack_name}_backend" -q | head -1)"
if [ -z "$backend_cid" ]; then
  echo "Backend container is not running" >&2
  exit 1
fi

docker exec \
  -e "WAREHOUSE_OPERATOR_PASSWORD=${warehouse_operator_password}" \
  -e "WAREHOUSE_MANAGER_PASSWORD=${warehouse_manager_password}" \
  -e "BUSINESS_OWNER_USER=${business_owner_user}" \
  -e "BUSINESS_OWNER_PASSWORD=${business_owner_password}" \
  -e "CLIENT_DESK_PASSWORD=${client_desk_password}" \
  "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} execute erpnext_3pl.validation.warehouse_ops.main"
