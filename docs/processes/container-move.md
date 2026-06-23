# Container Move

## Goal

Record an explicit operation when a warehouse worker moves a Handling Unit from one location to another.

This is the first operational layer above the base Handling Unit model.

## Current Model

The operation is stored as `Three PL Container Move`.

It stores:

- operation reference;
- operation time;
- status;
- container / Handling Unit;
- client;
- source location;
- target location;
- optional stock entry;
- linked movement history record;
- notes.

The movement history is stored separately in `Three PL Container Movement`.

## Current MVP Behavior

The current repository creates the DocType, report, permissions, demo operation, move processor, and validation.

Demo operation:

- Operation Reference: `MOVE-ALPHA-001`
- Container: `BOX-ALPHA-002`
- From: `Temporary Receiving - 3`
- To: `Aisle A - 3`
- Status: `Applied`

The demo operation starts as `Draft` during demo-data loading. `erpnext_3pl.warehouse.container_moves` applies it, updates the container current location, creates a `Three PL Container Movement` record, and marks the operation as `Applied`.

## Important Boundary

The scanner-first page applies container moves immediately through the versioned custom app API.

Submit-time automation directly from the ERPNext `Three PL Container Move` form is not implemented yet. If users create Draft move records manually in Desk, the versioned processor remains available as a recovery/batch path.

## Target Flow

1. Operator scans or selects the container.
2. System shows current location.
3. Operator scans or selects the target location.
4. Operator confirms the move.
5. System updates container current location.
6. System writes a `Three PL Container Movement` record.
7. System updates inventory snapshot if needed.

## Processor

Run pending moves inside the ERPNext backend through the app method:

```bash
cd /home/frappe/frappe-bench
bench --site SITE_NAME execute erpnext_3pl.warehouse.container_moves.main
```

The post-deploy script already runs this processor.

## Scanner-First Page

The repository creates a minimal scanner page:

`/warehouse/container-move`

The page lets a warehouse user scan or enter:

- container / HU;
- target location.

It creates and applies a `Three PL Container Move` immediately through `erpnext_3pl.api.warehouse_ops.apply_container_move`.

Current behavior:

- guest users are redirected to login;
- authenticated users can open the page;
- actual move creation and apply are protected by DocType permissions;
- the page creates a move operation;
- the page immediately writes movement history;
- the page updates the container current location and status;
- the page marks the move as `Applied`.

The processor remains available for batch application and recovery of Draft moves.

## Related Reports

- `3PL Container Moves`
- `3PL Container Movements`
- `3PL Containers`
