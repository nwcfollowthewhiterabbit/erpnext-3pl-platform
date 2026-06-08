# Container Repack

## Goal

Record and apply a warehouse operation where one or more source Handling Units are consolidated or repacked into a target Handling Unit.

Typical example:

- two smaller boxes are replaced by one larger box;
- source boxes should remain traceable;
- target box becomes the active container with the resulting contents.

## Current Model

The operation is stored as `Three PL Container Repack`.

It stores:

- operation reference;
- operation time;
- status;
- client;
- target container;
- target location;
- source containers;
- resulting item rows;
- linked movement history record;
- notes.

Source rows are stored in `Three PL Repack Source`.

Resulting item rows are stored in `Three PL Repack Item`.

Movement history is stored in `Three PL Container Movement`.

## Current MVP Behavior

The repository creates the DocTypes, report, permissions, demo operation, repack processor, and validation.

Demo operation:

- Operation Reference: `REPACK-ALPHA-001`
- Source Containers: `BOX-ALPHA-003`, `BOX-ALPHA-004`
- Target Container: `BOX-ALPHA-005`
- Target Location: `Aisle A - 3`
- Status after processor: `Applied`

`scripts/apply_container_repacks.py` applies draft repacks:

- validates source container ownership;
- rejects shipped, closed, or already replaced source containers;
- validates that source item quantities match target item quantities;
- creates or updates the target container;
- copies resulting item rows into the target container;
- marks source containers as `Replaced`;
- links source containers to the target through `replaced_by`;
- creates a `Three PL Container Movement` record with type `Repacked`;
- marks the repack operation as `Applied`.

## Scanner-First Page

Warehouse users can open:

`/warehouse/repack`

The current scanner flow supports full consolidation:

1. scan one or more source containers;
2. scan or enter the target container;
3. scan or enter the target location;
4. apply repack.

The page automatically aggregates all item rows from the source containers into the target container.

Expected result:

- a `Three PL Container Repack` operation is created;
- a `Three PL Container Movement` row is written with movement type `Repacked`;
- source containers are marked `Replaced`;
- source containers point to the target container through `replaced_by`;
- the target container becomes `Stored` at the target location;
- target container contents equal the sum of source container contents.

## Important Boundary

This is a controlled MVP repack flow. It applies the resulting contents entered on the repack operation.

Still pending:

- ERPNext form submit-time automation;
- richer item-level split guidance for partial repacks.

## Target Flow

1. Operator scans or selects source containers.
2. Operator scans or creates target container.
3. Operator confirms target location.
4. Operator confirms resulting item quantities.
5. System marks source containers as replaced.
6. System creates or updates target container contents.
7. System writes movement history.
8. System updates inventory snapshot if needed.

## Related Reports

- `3PL Container Repacks`
- `3PL Container Movements`
- `3PL Containers`
