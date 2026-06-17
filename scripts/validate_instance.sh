#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

base_url="${1:-}"

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

if [ -z "$base_url" ]; then
  base_url="http://127.0.0.1:${FRONTEND_PORT:-8080}"
fi

case "$base_url" in
  http://*|https://*) ;;
  *) base_url="https://${base_url}" ;;
esac

expected_bad="$(
  docker stack services "$stack_name" --format "{{.Name}} {{.Replicas}}" |
    awk '
      $1 ~ /_(configurator|create-site)$/ { next }
      $2 != "1/1" { print }
    '
)"

if [ -n "$expected_bad" ]; then
  echo "Unexpected service replica state:" >&2
  echo "$expected_bad" >&2
  exit 1
fi

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
  "cd /home/frappe/frappe-bench && bench --site ${site_name} execute erpnext_3pl.validation.site.main"

check_login() {
  user="$1"
  password="$2"
  cookie_file="$(mktemp)"
  response_file="$(mktemp)"
  page_file="$(mktemp)"

  curl -sS --max-time 30 \
    -X POST "${base_url%/}/api/method/login" \
    --data-urlencode "usr=${user}" \
    --data-urlencode "pwd=${password}" \
    -c "$cookie_file" > "$response_file"

  python3 - "$response_file" <<'PY'
import json
import sys

with open(sys.argv[1]) as handle:
    data = json.load(handle)

if data.get("message") != "Logged In":
    raise SystemExit(f"login failed: {data}")

if data.get("home_page") not in {"/desk/3pl-warehouse", "/desk", "/app/home", "/apps"}:
    raise SystemExit(f"unexpected home_page: {data}")
PY

  check_page() {
    path="$1"
    curl -fsSL --max-time 30 -b "$cookie_file" "${base_url%/}${path}" -o "$page_file"
    if grep -Eiq "Page not found|Not permitted|No permission" "$page_file"; then
      echo "Unexpected error page for ${user} at ${path}" >&2
      grep -Eio "Page not found|Not permitted|No permission" "$page_file" | head -5 >&2
      exit 1
    fi
  }

  check_page "/desk/3pl-warehouse"
  check_page "/desk"
  if [ "$user" = "$business_owner_user" ]; then
    check_page "/app/item"
    check_page "/app/warehouse"
    check_page "/app/uom"
  fi

  rm -f "$cookie_file" "$response_file" "$page_file"
}

check_login "warehouse.demo@example.test" "$warehouse_operator_password"
check_login "warehouse.manager@example.test" "$warehouse_manager_password"
check_login "$business_owner_user" "$business_owner_password"

check_client_desk_login() {
  user="$1"
  password="$2"
  cookie_file="$(mktemp)"
  response_file="$(mktemp)"
  page_file="$(mktemp)"

  curl -sS --max-time 30 \
    -X POST "${base_url%/}/api/method/login" \
    --data-urlencode "usr=${user}" \
    --data-urlencode "pwd=${password}" \
    -c "$cookie_file" > "$response_file"

  python3 - "$response_file" <<'PY'
import json
import sys

with open(sys.argv[1]) as handle:
    data = json.load(handle)

if data.get("message") != "Logged In":
    raise SystemExit(f"client Desk login failed: {data}")

if data.get("home_page") not in {"/desk/3pl-client", "/desk", "/app/home", "/desk/home"}:
    raise SystemExit(f"unexpected client Desk home_page: {data}")
PY

  for path in /desk/home /desk/3pl-client; do
    curl -fsSL --max-time 30 -b "$cookie_file" "${base_url%/}${path}" -o "$page_file"
    if grep -Eiq "Page not found|Not permitted|No permission" "$page_file"; then
      echo "Unexpected client Desk error page for ${user} at ${path}" >&2
      grep -Eio "Page not found|Not permitted|No permission" "$page_file" | head -5 >&2
      exit 1
    fi
  done

  rm -f "$cookie_file" "$response_file" "$page_file"
}

check_client_desk_login "alpha.client@example.test" "$client_desk_password"

echo "Instance validation passed for ${base_url}"
