#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

base_url="${1:-}"

if [ ! -f .env ]; then
  echo ".env is missing; copy .env.example and fill secrets" >&2
  exit 1
fi

set -a
. ./.env
set +a

stack_name="${STACK_NAME:?set STACK_NAME}"
site_name="${SITE_NAME:?set SITE_NAME}"

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

docker cp scripts/run_project_script.py "$backend_cid":/tmp/run_project_script.py
docker cp scripts/validate_site.py "$backend_cid":/tmp/validate_site.py
docker exec "$backend_cid" bash -lc \
  "cd /home/frappe/frappe-bench && ./env/bin/python /tmp/run_project_script.py ${site_name} /tmp/validate_site.py 0"

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

if data.get("home_page") not in {"/app/3pl-warehouse", "/app/home"}:
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

  check_page "/app/3pl-warehouse"
  check_page "/desk/3pl-warehouse"
  case "$base_url" in
    http://127.0.0.1:*|http://localhost:*) ;;
    *) check_page "/" ;;
  esac

  rm -f "$cookie_file" "$response_file" "$page_file"
}

check_login "warehouse.demo@example.test" "WarehouseDemo2026!"
check_login "warehouse.manager@example.test" "WarehouseManager2026!"

check_portal_login() {
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

if data.get("message") not in {"Logged In", "No App"}:
    raise SystemExit(f"portal login failed: {data}")

if data.get("home_page") not in {"/client/receiving-notice", "client/receiving-notice", "/me"}:
    raise SystemExit(f"unexpected portal home_page: {data}")
PY

  for path in /client/receiving-notice /client/inventory /client/shipment-request /client/discrepancy-instruction; do
    curl -fsSL --max-time 30 -b "$cookie_file" "${base_url%/}${path}" -o "$page_file"
    if grep -Eiq "Page not found|Not permitted|No permission" "$page_file"; then
      echo "Unexpected portal error page for ${user} at ${path}" >&2
      grep -Eio "Page not found|Not permitted|No permission" "$page_file" | head -5 >&2
      exit 1
    fi
  done

  rm -f "$cookie_file" "$response_file" "$page_file"
}

check_portal_login "alpha.client@example.test" "AlphaClient2026!"

expect_redirect() {
  path="$1"
  expected="$2"
  redirect="$(curl -sS -o /dev/null -w "%{redirect_url}" --max-time 30 "${base_url%/}${path}")"
  if [ "$redirect" != "${base_url%/}${expected}" ]; then
    echo "Unexpected redirect for ${path}: ${redirect}" >&2
    exit 1
  fi
}

case "$base_url" in
  http://127.0.0.1:*|http://localhost:*) ;;
  *)
    expect_redirect "/" "/app/3pl-warehouse"
    expect_redirect "/app/setup-wizard" "/app/3pl-warehouse"
    expect_redirect "/app/setup-wizard/" "/app/3pl-warehouse"
    expect_redirect "/login?redirect-to=%2Fapp%2Fsetup-wizard" "/login?redirect-to=%2Fapp%2F3pl-warehouse"
    expect_redirect "/app/home" "/app/3pl-warehouse"
    ;;
esac

echo "Instance validation passed for ${base_url}"
