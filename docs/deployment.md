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
./deploy.sh https://erpnext.77.237.244.169.sslip.io
./scripts/validate_instance.sh https://erpnext.77.237.244.169.sslip.io
```

`deploy.sh` delegates to `scripts/deploy_existing_instance.sh`. For an existing site, that script creates a backup with files, pulls the pinned `ERPNEXT_IMAGE`, deploys the stack, runs `bench migrate`, reapplies the warehouse setup scripts, and validates the instance. Do not upgrade a running ERPNext instance with only `docker stack deploy`; major version changes require the migration step.

`run_post_deploy.sh` is idempotent. It reapplies warehouse-only mode, custom workspaces, reports, roles, demo users, and demo data.

## Regional Defaults

- Country: `Lithuania`
- Currency: `EUR`
- Language: `English` (`en`)
- Time zone: `Europe/Vilnius` (Vilnius local time, UTC+3 during summer time)

## Email Placeholder

The deployment creates a placeholder default outgoing Email Account:

- Name: `Placeholder Outgoing Email`
- Email: `noreply@example.invalid`
- SMTP: `smtp.placeholder.invalid:25`

This is only a temporary default so ERPNext forms that require an outgoing account can proceed. Real outbound email delivery and newsletters are not configured yet.

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

It also redirects stale setup wizard links to `/app/3pl-warehouse`. This includes both direct `/app/setup-wizard` requests and `/login?redirect-to=%2Fapp%2Fsetup-wizard`, because Frappe's login page honors the `redirect-to` query parameter after successful browser login.

On ERPNext v16, the ERPNext app route is `/app/home` by default. This warehouse-first instance redirects `/app/home` to `/app/3pl-warehouse` at the public nginx layer so browser login lands in the 3PL workspace without forking the upstream Docker image. The public root `/` redirects to `/login` without a forced `redirect-to`, so Frappe can send each role to its configured home page: client users to the portal and warehouse users to the 3PL workspace.

## Validation

Always run validation after deploy:

```bash
./scripts/validate_instance.sh https://erpnext.77.237.244.169.sslip.io
```

Validation checks:

- expected Swarm services are `1/1`
- setup wizard is marked complete for the installed Frappe/ERPNext apps
- regional defaults are Lithuania, EUR, English, and Europe/Vilnius
- placeholder default outgoing Email Account exists
- custom DocTypes, report, warehouses, workspaces, demo users, and demo data exist
- demo users have `Warehouse Only` module profile and default workspace `3PL Warehouse`
- public root redirects to `/login`, while demo login returns the configured role home page
- `/app/3pl-warehouse` is reachable for both demo users
- stale `/app/setup-wizard`, login `redirect-to` setup wizard URLs, and public `/app/home` redirect to the warehouse workspace

## Current Instance

- Server alias: `wherp`
- Public URL: `https://erpnext.77.237.244.169.sslip.io`
- Stack: `erpnext3pl`
- Site: `erpnext-3pl.local`
- Project path on server: `/opt/erpnext-3pl-platform`
