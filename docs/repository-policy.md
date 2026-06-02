# Repository Policy

This repository must preserve every operational detail needed to recreate the ERPNext 3PL instance.

## Source of Truth

All deploy, configuration, demo-data, permission, workspace, report, nginx, TLS, and validation behavior belongs in versioned files. Server shell commands are acceptable for investigation, but any command that becomes part of the fix must be converted into a script or documented step before the work is considered complete.

## Required For Every Infrastructure Change

1. Add or update code in `compose*.yml`, `deploy.sh`, or `scripts/`.
2. Add or update explanation in `README.md`, `docs/deployment.md`, or a focused manual under `docs/`.
3. Make scripts idempotent unless there is a documented reason they cannot be.
4. Add validation for the behavior when practical.
5. Run syntax checks before commit:

```bash
bash -n deploy.sh scripts/*.sh
python3 -m py_compile scripts/*.py
```

## No Hidden Manual Fixes

Do not rely on:

- shell history
- hand-created ERPNext records
- undocumented server packages
- one-off SQL updates
- browser-only configuration

If the instance needs a role, workspace, report, custom field, user default, nginx vhost, TLS certificate flow, or demo record, encode it in the repository.

## First Deploy Standard

A clean server must pass:

```bash
sudo scripts/bootstrap_docker_swarm.sh SERVER_IP
cp .env.example .env
$EDITOR .env
sudo ./scripts/deploy_first_instance.sh erpnext.SERVER_IP.sslip.io
./scripts/validate_instance.sh https://erpnext.SERVER_IP.sslip.io
```

The validation command is the acceptance test for a deployable repository.
