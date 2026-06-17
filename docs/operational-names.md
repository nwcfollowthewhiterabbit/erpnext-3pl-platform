# Operational Names

This file is the quick lookup for names that must stay consistent across deploy scripts, Docker Swarm, bench commands, nginx, and manual testing.

## Current Live Instance

| Item | Value |
| --- | --- |
| SSH alias | `wherp` |
| Project path | `/opt/erpnext-3pl-platform` |
| Public URL | `https://erpnext.77.237.244.169.sslip.io` |
| Client Desk URL | `https://erpnext.77.237.244.169.sslip.io/desk/3pl-client` |
| Warehouse Desk URL | `https://erpnext.77.237.244.169.sslip.io/desk/3pl-warehouse` |
| Live Swarm stack | `erpnext3pl` |
| Staging Swarm stack | `erpnext3plstg` |
| ERPNext site name | `erpnext-3pl.local` |
| Custom app | `erpnext_3pl` |
| Custom app module | `ERPNext 3PL` |
| Public nginx vhost | `/etc/nginx/sites-enabled/erpnext.77.237.244.169.sslip.io` |
| Live env file | `/opt/erpnext-3pl-platform/.env` |
| Staging env file | `/opt/erpnext-3pl-platform/.env.staging` |

## Docker Names

Live containers are Swarm task containers, so their names include dynamic suffixes. Do not hard-code the full container name.

Use these prefixes:

| Purpose | Container prefix |
| --- | --- |
| Live backend | `erpnext3pl_backend` |
| Live frontend | `erpnext3pl_frontend` |
| Live scheduler | `erpnext3pl_scheduler` |
| Live short queue | `erpnext3pl_queue-short` |
| Live long queue | `erpnext3pl_queue-long` |
| Live DB | `erpnext3pl_db` |
| Staging backend | `erpnext3plstg_backend` |
| Staging frontend | `erpnext3plstg_frontend` |
| Staging DB | `erpnext3plstg_db` |

Recommended live backend lookup:

```bash
live_backend=$(docker ps --format '{{.Names}}' | grep '^erpnext3pl_backend' | head -1)
```

Recommended staging backend lookup:

```bash
staging_backend=$(docker ps --format '{{.Names}}' | grep '^erpnext3plstg_backend' | head -1)
```

## Bench Commands

Always use the internal site name, not the public domain:

```bash
docker exec -it "$live_backend" bench --site erpnext-3pl.local list-apps
docker exec -it "$live_backend" bench --site erpnext-3pl.local clear-cache
```

Do not run broad site setup as part of normal development/deploy iterations. Environment bootstrap is limited to focused commands such as `erpnext_3pl.bootstrap.site.main`. MVP DocTypes, fields, roles, permissions, workflows, reports, warehouse pages, stock entry types, and Workspaces should come from app files or fixtures.

## Users, Roles, And Workspaces

| Actor | Login | Role | Module Profile | Default Workspace | Desk URL |
| --- | --- | --- | --- | --- | --- |
| Client | `alpha.client@example.test` | `3PL Client` | `3PL Client Only` | `3PL Client` | `/desk/3pl-client` |
| Warehouse operator | `warehouse.demo@example.test` | `3PL Warehouse User` | `Warehouse Only` | `3PL Warehouse` | `/desk/3pl-warehouse` |
| Warehouse manager | `warehouse.manager@example.test` | `3PL Warehouse Manager` | `Warehouse Only` | `3PL Warehouse` | `/desk/3pl-warehouse` |
| Business owner | `business.owner@example.test` | `3PL Warehouse Manager` plus admin roles | none | `3PL Warehouse` | `/desk/3pl-warehouse` |

Passwords are not stored in documentation. Read them from `.env` or `.env.staging`.

The client user is a Desk `System User`, not a legacy Website Portal user. The client should not keep the standard `Customer` role; customer isolation is handled by `User Permission` on `Customer = Demo Client Alpha` plus `3PL Client` DocPerms.

## Route Rules

- Use `/desk/3pl-client` for the client workspace.
- Use `/desk/3pl-warehouse` for warehouse users.
- `/desk/3pl-client` is the canonical client workspace link.
- Client testing should use the native ERPNext Desk workspace.
- nginx should not force `/app`, `/desk`, `/app/home`, or `/apps` to the warehouse workspace. Let ERPNext handle Desk routing by role/workspace.
- Current stable baseline: `docs/stable-native-baseline.md`.

## Quick Live Checks

```bash
curl -ks -o /dev/null -w '%{http_code} %{redirect_url}\n' \
  https://erpnext.77.237.244.169.sslip.io/desk/3pl-client

ssh wherp 'docker ps --format "{{.Names}}" | grep "^erpnext3pl_backend" | head -1'
```
