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

base_image="${BASE_IMAGE:-frappe/erpnext:v16.0.0}"
erpnext_image="${ERPNEXT_IMAGE:?set ERPNEXT_IMAGE}"
deploy_push_image="${DEPLOY_PUSH_IMAGE:-0}"
deploy_local_registry="${DEPLOY_LOCAL_REGISTRY:-0}"
local_registry_name="${LOCAL_REGISTRY_NAME:-erpnext-3pl-registry}"
local_registry_port="${LOCAL_REGISTRY_PORT:-5000}"

if [ "$deploy_local_registry" = "1" ]; then
  if ! docker ps --format "{{.Names}}" | grep -qx "$local_registry_name"; then
    if docker ps -a --format "{{.Names}}" | grep -qx "$local_registry_name"; then
      docker start "$local_registry_name" >/dev/null
    else
      docker run -d \
        --restart=always \
        --name "$local_registry_name" \
        -p "127.0.0.1:${local_registry_port}:5000" \
        registry:2 >/dev/null
    fi
  fi
fi

docker build \
  --build-arg "BASE_IMAGE=${base_image}" \
  -t "$erpnext_image" \
  .

if [ "$deploy_push_image" = "1" ]; then
  docker push "$erpnext_image"
fi
