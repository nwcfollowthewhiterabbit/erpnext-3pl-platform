# Deployment

This repository is the source of truth for provisioning and configuring the ERPNext 3PL instance. A fresh instance should be deployable from these files without copying manual steps from chat history or server shell history.

## Fresh Server

Run these commands on the target server from a checked-out copy of this repository:

```bash
sudo scripts/bootstrap_docker_swarm.sh SERVER_IP
cp .env.example .env
$EDITOR .env
sudo ./scripts/deploy_first_instance.sh erpnext.SERVER_IP.sslip.io
```

`deploy_first_instance.sh` is intentionally different from `deploy.sh`. On a fresh site, ERPNext `bench new-site` must run without backend, frontend, workers, scheduler, or websocket competing for the partially created database. The first-deploy script uses `compose.bootstrap.yml` to keep runtime services scaled to zero until `create-site` finishes, then deploys the normal stack.

## Existing Instance Update

Use the normal update path when the site already exists:

```bash
./deploy.sh
./scripts/run_post_deploy.sh
./scripts/validate_instance.sh https://erpnext.77.237.244.169.sslip.io
```

`run_post_deploy.sh` is idempotent. It reapplies warehouse-only mode, custom workspaces, reports, roles, demo users, and demo data.

## HTTPS

For a quick public HTTPS endpoint without DNS administration, use `sslip.io`:

```bash
sudo scripts/configure_https.sh erpnext.SERVER_IP.sslip.io
```

For a real domain, point its A record to the server first, then pass that domain:

```bash
sudo scripts/configure_https.sh erp.example.com
```

The script installs nginx/certbot, proxies to the ERPNext frontend on port `8080`, enables HTTP to HTTPS redirects, and leaves certbot renewal enabled.

## Validation

Always run validation after deploy:

```bash
./scripts/validate_instance.sh https://erpnext.77.237.244.169.sslip.io
```

Validation checks:

- expected Swarm services are `1/1`
- custom DocTypes, report, warehouses, workspaces, demo users, and demo data exist
- demo users have `Warehouse Only` module profile and default workspace `3PL Warehouse`
- demo login redirects to `/app/3pl-warehouse`
- `/app/3pl-warehouse` is reachable for both demo users

## Current Instance

- Server alias: `wherp`
- Public URL: `https://erpnext.77.237.244.169.sslip.io`
- Stack: `erpnext3pl`
- Site: `erpnext-3pl.local`
- Project path on server: `/opt/erpnext-3pl-platform`
