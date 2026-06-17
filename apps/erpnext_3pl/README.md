# ERPNext 3PL Frappe App

This directory contains the staged Frappe app extraction for the ERPNext 3PL platform.

## Current Scope

The app currently owns the reusable Python business logic:

- client product synchronization
- receiving notice discrepancy synchronization
- inventory snapshot synchronization
- shipment request allocation and Pick List creation
- picking confirmation synchronization
- outbound fulfillment synchronization
- container moves, repacks, and warehouse correction processors
- MVP validation modules

The app also defines `doc_events` hooks in `erpnext_3pl/hooks.py` that map the live Server Script behavior to Python hook handlers.

The schema and UI configuration is tracked through app-owned assets:

- Custom DocTypes and their child tables as first-class DocType JSON modules
- Custom Fields on ERPNext documents
- 3PL roles, custom permissions, module profiles, and stock entry types
- 3PL workflows, reports, warehouse web pages, Workspaces, and the warehouse rename property setter

## Migration Boundary

Normal deploys rely on app DocType modules, fixtures, workflow fixtures, and native Workspace files as the source of truth for schema/UI records. Environment bootstrap is limited to focused commands such as `erpnext_3pl.bootstrap.site.main`; it should not generate app-owned schema, Workspaces, reports, pages, or workflows.

Do not install this app on the live site together with the existing generated Server Scripts unless those duplicate Server Scripts are disabled first. Otherwise, the same document events can run twice.

The next migration step is to reduce environment bootstrap further once defaults can be represented as fixtures, patches, or app-owned records.

## Fixture Export

After changing setup-owned schema or UI records on a bench site:

```bash
bench --site <site> execute erpnext_3pl.scripts.export_fixtures.export
bench --site <site> execute erpnext_3pl.scripts.export_fixtures.export_workspaces
```

Review the generated files under `erpnext_3pl/fixtures/` before committing them.

## Local Checks

From the repository root:

```bash
python3 -m py_compile $(find apps/erpnext_3pl -name '*.py')
python3 scripts/validate_repo.py
```
