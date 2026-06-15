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

Submitting or saving an `Inbound Shipment Notice` does not create client inventory by itself. A notice is only the client's advance notification of an expected inbound shipment. Client-facing inventory is updated after warehouse-side receiving creates or updates active Handling Units / containers, and then the inventory snapshot processor synchronizes those containers into `Three PL Inventory Snapshot`.

This boundary is intentional: showing inventory immediately after client notice submission would make the portal display stock before the warehouse physically receives and verifies the goods.

The repository also provides:

- detailed report: `3PL Client Inventory`;
- aggregated report: `3PL Client Inventory Summary`.
- daily historical report: `3PL Inventory Balance By Date`.

## Daily Balance History

`scripts/sync_inventory_balance_snapshots.py` copies current inventory snapshot rows into `Three PL Inventory Balance Snapshot`.

This creates one daily balance history row per:

- date;
- client;
- item;
- warehouse location;
- container;
- inventory status.

The report `3PL Inventory Balance By Date` reads this history. It is intended for the MVP requirement "product balance on a selected date". History starts from the first day the processor is run; it does not reconstruct dates before the system started storing daily snapshots.

The processor runs during post-deploy after `sync_inventory_snapshots.py`. It can also be run on a schedule once production operations start.

Still pending:

- stock-ledger reconciliation;
- shipment allocation logic.
