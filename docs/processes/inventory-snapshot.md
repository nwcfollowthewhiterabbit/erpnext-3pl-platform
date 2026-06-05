# Inventory Snapshot Sync

## Goal

Keep `Three PL Inventory Snapshot` aligned with active Handling Units.

The snapshot is the client-facing inventory view. It should not depend only on manually seeded demo data.

## Current Processor

`scripts/sync_inventory_snapshots.py`

The processor:

- reads active `Three PL Container` records;
- creates or updates one snapshot row per client + item + container;
- copies current location from the container;
- maps container status to snapshot status;
- deletes stale container-based snapshots for inactive/replaced containers.

Active container statuses:

- Received
- In Verification
- Ready for Putaway
- Stored
- Picking
- Picked
- Packed

Status mapping:

- receiving/verification/putaway-ready -> `Receiving`
- stored -> `Available`
- picking/picked/packed -> `Allocated`

## Current Boundary

The processor is versioned and runs during post-deploy. It can also be run after operational batches.

Still pending:

- automatic run after every scanner operation;
- stock-ledger reconciliation;
- shipment allocation logic.
