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

site_name="${SITE_NAME:?set SITE_NAME}"
stack_name="${STACK_NAME:?set STACK_NAME}"

backend_service="${stack_name}_backend"
backend_cid="$(docker ps --filter "label=com.docker.swarm.service.name=${backend_service}" -q | head -1)"

if [ -z "$backend_cid" ]; then
  echo "Backend container for ${backend_service} is not running" >&2
  exit 1
fi

docker cp scripts/run_project_script.py "$backend_cid":/tmp/run_project_script.py
docker cp scripts/project_config.py "$backend_cid":/tmp/project_config.py
docker cp scripts/configure_warehouse_mode.py "$backend_cid":/tmp/configure_warehouse_mode.py
docker cp scripts/create_demo_users.py "$backend_cid":/tmp/create_demo_users.py
docker cp scripts/load_demo_warehouse_data.py "$backend_cid":/tmp/load_demo_warehouse_data.py

project_env=(
  -e "WAREHOUSE_OPERATOR_PASSWORD=${WAREHOUSE_OPERATOR_PASSWORD:?set WAREHOUSE_OPERATOR_PASSWORD}"
  -e "WAREHOUSE_MANAGER_PASSWORD=${WAREHOUSE_MANAGER_PASSWORD:?set WAREHOUSE_MANAGER_PASSWORD}"
  -e "BUSINESS_OWNER_USER=${BUSINESS_OWNER_USER:?set BUSINESS_OWNER_USER}"
  -e "BUSINESS_OWNER_PASSWORD=${BUSINESS_OWNER_PASSWORD:?set BUSINESS_OWNER_PASSWORD}"
  -e "CLIENT_PORTAL_PASSWORD=${CLIENT_PORTAL_PASSWORD:?set CLIENT_PORTAL_PASSWORD}"
)

docker exec -u root "$backend_cid" bash -lc \
  "mkdir -p /home/frappe/logs /home/frappe/frappe-bench/sites/${site_name}/logs && chown -R frappe:frappe /home/frappe/logs /home/frappe/frappe-bench/sites/${site_name}/logs"

docker exec "${project_env[@]}" "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ./env/bin/python /tmp/run_project_script.py ${site_name} /tmp/configure_warehouse_mode.py 0"
docker exec "${project_env[@]}" "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ./env/bin/python /tmp/run_project_script.py ${site_name} /tmp/create_demo_users.py 1"
docker exec "${project_env[@]}" "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ./env/bin/python /tmp/run_project_script.py ${site_name} /tmp/load_demo_warehouse_data.py 1"
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && bench --site ${site_name} clear-cache"

./scripts/validate_instance.sh "http://127.0.0.1:${FRONTEND_PORT:-8080}"

echo "Post-deploy warehouse setup complete for ${site_name}"
