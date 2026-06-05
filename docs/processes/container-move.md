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

The demo operation starts as `Draft` during demo-data loading. `scripts/apply_container_moves.py` applies it, updates the container current location, creates a `Three PL Container Movement` record, and marks the operation as `Applied`.

## Important Boundary

At this stage, the move operation can be applied by the versioned processor script. Submit-time automation directly from the ERPNext form is not implemented yet.

The next implementation decision is whether automation should be done through:

- a custom Frappe app with controller logic;
- Server Scripts, if enabled and accepted for the deployment;
- a dedicated scanner/mobile operation page.

The preferred long-term direction is a custom app or scanner-first operation page, because it is easier to test, version, and validate than hidden manual server scripts. The processor script keeps the behavior versioned and testable until that UI/controller layer is added.

## Target Flow

1. Operator scans or selects the container.
2. System shows current location.
3. Operator scans or selects the target location.
4. Operator confirms the move.
5. System updates container current location.
6. System writes a `Three PL Container Movement` record.
7. System updates inventory snapshot if needed.

## Processor

Run pending moves inside the ERPNext backend through the project runner:

```bash
cd /home/frappe/frappe-bench
./env/bin/python /tmp/run_project_script.py SITE_NAME /tmp/apply_container_moves.py 0
```

The post-deploy script already copies and runs this processor.

## Scanner-First Page

The repository creates a minimal scanner page:

`/warehouse/container-move`

The page lets a warehouse user scan or enter:

- container / HU;
- target location.

It creates a Draft `Three PL Container Move`. The versioned processor applies pending moves.

## Related Reports

- `3PL Container Moves`
- `3PL Container Movements`
- `3PL Containers`
