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

## MVP1 Scope Source Of Truth

Use `docs/client-mvp-scope-status.md` as the source of truth for what belongs to customer-requested MVP1.

Important boundaries:

- Product Import / bulk import is not part of MVP1 acceptance.
- `Three PL Client Product Import` may exist in code as a roadmap/admin capability, but it must not be exposed as a required client MVP1 flow.
- MVP1 product maintenance is `Three PL Client Product` create/edit plus sync to ERPNext `Item`.
- Product Export is available for review/reporting, but it is not the same as Product Import.
- Receiving Scan is a convenience warehouse page over the same receiving logic; MVP1 receiving can also be tested through submitted `Stock Entry` type `3PL Inbound Receipt`.
- `Inbound Shipment Notice` alone is an expected-shipment notice and does not create stock, containers, or `Current Inventory`.
- `Stock Entry.purpose` is visible/read-only in this project. Manual instructions may tell testers to verify it, but not to edit it. The value is derived from `Stock Entry Type`.

## Route Rules

- Use `/desk/3pl-client` for the client workspace.
- Use `/desk/3pl-warehouse` for warehouse users.
- `/desk/3pl-client` is the canonical client workspace link.
- Client testing should use the native ERPNext Desk workspace.
- nginx should not force `/app`, `/desk`, `/app/home`, or `/apps` to the warehouse workspace. Let ERPNext handle Desk routing by role/workspace.
- Current stable baseline: `docs/stable-native-baseline.md`.

## Report Access Rules

Report access is controlled by ERPNext Desk configuration, not by custom pages:

- `Report.ref_doctype` must be correct.
- The role must have both `read = 1` and `report = 1` on the report `ref_doctype`.
- Workspace report links must include `report_ref_doctype`.
- The shared `ERPNext 3PL` module must use the explicit `Workspace Sidebar` named `ERPNext 3PL`; do not rely on the autogenerated module sidebar for client/warehouse mixed access.
- After changing Workspace Sidebar records, restart the live backend service because ERPNext caches generated sidebars in Python process memory.

Details and the incident pattern are documented in `docs/stable-native-baseline.md`.

## Quick Live Checks

```bash
curl -ks -o /dev/null -w '%{http_code} %{redirect_url}\n' \
  https://erpnext.77.237.244.169.sslip.io/desk/3pl-client

ssh wherp 'docker ps --format "{{.Names}}" | grep "^erpnext3pl_backend" | head -1'
```
