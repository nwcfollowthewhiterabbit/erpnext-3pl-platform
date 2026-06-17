#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

find \
  apps/erpnext_3pl/erpnext_3pl/fixtures \
  apps/erpnext_3pl/erpnext_3pl/erpnext_3pl/workspace \
  apps/erpnext_3pl/erpnext_3pl/erpnext_3pl/doctype \
  -type f -name '*.json' -print |
  sort |
  xargs -n1 python3 -m json.tool >/dev/null

python3 -m py_compile $(find apps/erpnext_3pl -name '*.py') scripts/validate_repo.py
python3 scripts/validate_repo.py
bash -n scripts/*.sh deploy.sh

if [ "${CI_BUILD_IMAGE:-0}" = "1" ]; then
  ./scripts/build_app_image.sh
fi

if [ "${CI_CLEAN_STACK:-0}" = "1" ]; then
  env_file="${PROJECT_ENV_FILE:-.env.ci}"
  if [ ! -f "$env_file" ]; then
    echo "$env_file is required when CI_CLEAN_STACK=1" >&2
    exit 1
  fi

  PROJECT_ENV_FILE="$env_file" ./scripts/deploy_first_instance.sh
  PROJECT_ENV_FILE="$env_file" ./scripts/validate_mvp_e2e.sh
  PROJECT_ENV_FILE="$env_file" ./scripts/validate_warehouse_ops.sh
fi

echo "CI smoke validation passed"
