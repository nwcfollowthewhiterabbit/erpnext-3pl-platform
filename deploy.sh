#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

exec ./scripts/deploy_existing_instance.sh "$@"
