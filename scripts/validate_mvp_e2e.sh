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
warehouse_operator_password="${WAREHOUSE_OPERATOR_PASSWORD:?set WAREHOUSE_OPERATOR_PASSWORD}"
warehouse_manager_password="${WAREHOUSE_MANAGER_PASSWORD:?set WAREHOUSE_MANAGER_PASSWORD}"
business_owner_user="${BUSINESS_OWNER_USER:?set BUSINESS_OWNER_USER}"
business_owner_password="${BUSINESS_OWNER_PASSWORD:?set BUSINESS_OWNER_PASSWORD}"
client_portal_password="${CLIENT_PORTAL_PASSWORD:?set CLIENT_PORTAL_PASSWORD}"

backend_cid="$(docker ps --filter "label=com.docker.swarm.service.name=${stack_name}_backend" -q | head -1)"
if [ -z "$backend_cid" ]; then
  echo "Backend container is not running" >&2
  exit 1
fi

for script in \
  run_project_script.py \
  project_config.py \
  sync_client_products.py \
  sync_receiving_notices.py \
  sync_inventory_snapshots.py \
  sync_inventory_balance_snapshots.py \
  sync_shipment_requests.py \
  sync_picking_confirmations.py \
  sync_outbound_fulfillment.py \
  validate_mvp_e2e.py
do
  docker cp "scripts/${script}" "$backend_cid":"/tmp/${script}"
done

docker exec \
  -e "WAREHOUSE_OPERATOR_PASSWORD=${warehouse_operator_password}" \
  -e "WAREHOUSE_MANAGER_PASSWORD=${warehouse_manager_password}" \
  -e "BUSINESS_OWNER_USER=${business_owner_user}" \
  -e "BUSINESS_OWNER_PASSWORD=${business_owner_password}" \
  -e "CLIENT_PORTAL_PASSWORD=${client_portal_password}" \
  "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ./env/bin/python /tmp/run_project_script.py ${site_name} /tmp/validate_mvp_e2e.py 1"
