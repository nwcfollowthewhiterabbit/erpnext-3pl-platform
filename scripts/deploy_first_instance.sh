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
domain="${1:-}"

wait_for_service_state() {
  service_name="$1"
  expected_pattern="$2"
  timeout_seconds="$3"
  start_ts="$(date +%s)"

  while true; do
    state="$(docker service ps "$service_name" --no-trunc --format "{{.CurrentState}} {{.Error}}" | head -1 || true)"
    echo "${service_name}: ${state:-missing}"

    if printf "%s" "$state" | grep -Eq "$expected_pattern"; then
      return 0
    fi

    if printf "%s" "$state" | grep -Eiq "Failed|Rejected"; then
      docker service logs --no-task-ids --raw --tail 120 "$service_name" 2>&1 || true
      echo "${service_name} failed: ${state}" >&2
      return 1
    fi

    if [ "$(( $(date +%s) - start_ts ))" -ge "$timeout_seconds" ]; then
      docker service logs --no-task-ids --raw --tail 120 "$service_name" 2>&1 || true
      echo "Timed out waiting for ${service_name}" >&2
      return 1
    fi

    sleep 10
  done
}

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

echo "Deploying bootstrap stack for ${site_name}"
docker stack deploy -c compose.yml -c compose.bootstrap.yml "$stack_name"

wait_for_service_state "${stack_name}_configurator" "Complete" 300
wait_for_service_state "${stack_name}_create-site" "Complete" 1200

echo "Deploying runtime stack"
docker stack deploy -c compose.yml "$stack_name"
wait_for_replicas 600

./scripts/run_post_deploy.sh

if [ -n "$domain" ]; then
  if [ "$(id -u)" -ne 0 ]; then
    echo "HTTPS configuration needs root; rerun with sudo or run scripts/configure_https.sh ${domain}" >&2
  else
    ./scripts/configure_https.sh "$domain" "${FRONTEND_PORT:-8080}"
  fi
fi

./scripts/validate_instance.sh "${domain:-http://127.0.0.1:${FRONTEND_PORT:-8080}}"
