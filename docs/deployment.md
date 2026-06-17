# Deployment

This repository is the source of truth for provisioning and configuring the ERPNext 3PL instance. A fresh instance should be deployable from these files without copying manual steps from chat history or server shell history.

For canonical stack names, site names, workspace routes, container prefixes, demo users, and common bench commands, see `docs/operational-names.md`.

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

`deploy.sh` delegates to `scripts/deploy_existing_instance.sh`. For an existing site, that script creates a backup with files, builds or pulls the pinned `ERPNEXT_IMAGE`, deploys the stack, runs `bench migrate`, reapplies the warehouse app bootstrap methods, and validates the instance. Do not upgrade a running ERPNext instance with only `docker stack deploy`; major version changes require the migration step.

The default `.env.example` uses a registry-backed custom image tag (`localhost:5000/erpnext-3pl-platform:latest`) with `DEPLOY_BUILD_IMAGE=1`, `DEPLOY_PUSH_IMAGE=1`, and `DEPLOY_LOCAL_REGISTRY=1`. This starts a local Docker registry on the deployment host, pushes the freshly built app image, and lets Docker Swarm resolve an image digest instead of deploying an untracked `:local` image. For a multi-node or production setup, replace `ERPNEXT_IMAGE` with a real registry path and keep `DEPLOY_PUSH_IMAGE=1`.

`run_post_deploy.sh` is intentionally light for normal updates. By default it verifies the installed app and clears cache; it does not replay site bootstrap, demo data, or recovery processors. Use explicit flags only when needed:

```bash
RUN_SITE_BOOTSTRAP=1 RUN_DEMO_DATA=1 RUN_RECOVERY_PROCESSORS=1 ./scripts/run_post_deploy.sh
```

Fresh deploy uses those flags once after site creation. Existing deploys should rely on app files, fixtures, workflow fixtures, migrations, and validation instead of re-running broad setup logic.

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

It keeps routing neutral for ERPNext Desk. nginx must not contain role, portal, setup-wizard, `/app`, `/desk`, or workspace-specific redirects.

Do not add nginx redirects that force `/app`, `/desk`, `/app/home`, or `/apps` into any workspace. MVP1 now uses native ERPNext Desk workspaces, so ERPNext should route users by role, module profile, and default workspace.

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
- custom DocTypes, workflows, reports, warehouses, workspaces, demo users, and demo data exist
- demo users have `Warehouse Only` module profile and default workspace `3PL Warehouse`
- public root redirects to `/login`, while demo login returns the configured role home page
- `/desk/3pl-warehouse` is reachable for warehouse demo users
- `/desk/3pl-client` is reachable for the client demo user

## Current Instance

- Server alias: `wherp`
- Public URL: `https://erpnext.77.237.244.169.sslip.io`
- Stack: `erpnext3pl`
- Staging stack: `erpnext3plstg`
- Site: `erpnext-3pl.local`
- Project path on server: `/opt/erpnext-3pl-platform`
- Client Desk URL: `https://erpnext.77.237.244.169.sslip.io/desk/3pl-client`
