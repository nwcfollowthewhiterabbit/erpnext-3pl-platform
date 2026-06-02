#!/usr/bin/env bash
set -euo pipefail

advertise_addr="${1:-}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y ca-certificates curl gnupg lsb-release

  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg.tmp
  chmod a+r /etc/apt/keyrings/docker.gpg.tmp
  mv /etc/apt/keyrings/docker.gpg.tmp /etc/apt/keyrings/docker.gpg

  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

systemctl enable --now docker

if ! docker info --format "{{.Swarm.LocalNodeState}}" | grep -qx active; then
  if [ -n "$advertise_addr" ]; then
    docker swarm init --advertise-addr "$advertise_addr"
  else
    docker swarm init
  fi
fi

docker --version
docker info --format "Swarm={{.Swarm.LocalNodeState}} NodeID={{.Swarm.NodeID}}"
