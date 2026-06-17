# Stable Native Baseline

Status date: 2026-06-17.

This is the clean stable starting point for MVP1 manual testing.

The project is now a native ERPNext Desk solution. The previous custom client interface, forced redirects, and route-specific nginx behavior are out of the active MVP path. nginx should remain a neutral HTTPS reverse proxy to the ERPNext frontend.

## Access Model

Access is controlled in ERPNext/Frappe, not in nginx:

- role `home_page`;
- user `default_workspace`;
- Module Profile;
- Workspace roles;
- DocType permissions;
- Customer `User Permission`;
- narrow data guards for customer-owned client documents and client-visible system data.

Canonical entry points:

- Client: `/desk/3pl-client`;
- Warehouse operator/manager: `/desk/3pl-warehouse`;
- Business owner: `/desk/3pl-warehouse`.

## Current Stable Constraints

- `3PL Client` is a Desk `System User`, not a legacy Website Portal user.
- `3PL Client` uses Module Profile `3PL Client Only`.
- Warehouse users use Module Profile `Warehouse Only`.
- Client and warehouse workspaces are role-scoped.
- The client user must not have `Customer`, `Stock User`, `Stock Manager`, `System Manager`, or warehouse roles.
- Client data access is scoped to `Demo Client Alpha` through Customer User Permission and app-level document guards.
- Client system access is intentionally narrow: the client may not list unrelated `User` records and may not read `Role`, `DocType`, `Module Profile`, or `System Settings`.

## Known Naming Debt

Some internal DocType fields still use legacy names such as `portal_source` and `portal_items_description`. They are compatibility/storage fields for client-originated Desk records, not an active custom portal. Renaming them should be handled later as a controlled schema migration, outside the clean baseline stabilization.

## Explicit Backlog

No server-side route/landing redirect guard is part of this baseline.

If manual testing shows that users often land in the wrong workspace after login or bookmarks, add a small Frappe-native route consistency guard later. That guard should only normalize landing routes; it must not reintroduce a custom client interface or nginx-based business routing.
