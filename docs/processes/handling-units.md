# Handling Units

## Business Decision

ERPNext does not provide a complete 3PL-style Handling Unit workflow out of the box.

The project models Handling Units through the custom `Three PL Container` DocType. This keeps the implementation close to standard ERPNext stock logic while adding the missing WMS layer for boxes, cartons, pallets, and other physical handling units.

## Current Model

`Three PL Container` represents a physical handling unit.

It stores:

- container / box code;
- barcode or label;
- container type: box, carton, pallet, tote, or other;
- owner client;
- current warehouse location;
- lifecycle status;
- parent container, for example a box on a pallet;
- replacement container, for repack or consolidation;
- last moved timestamp;
- item rows with SKU, client SKU, quantity, UOM, and condition.

Handling Unit movements are stored in `Three PL Container Movement`.

Movement records store:

- movement time;
- container / Handling Unit;
- client;
- movement type;
- source location;
- target location;
- source container;
- target container;
- reference document;
- notes.

Lifecycle statuses:

- Expected
- Received
- In Verification
- Ready for Putaway
- Stored
- Picking
- Picked
- Packed
- Shipped
- Empty
- Closed
- Replaced

## Operating Logic

Use ERPNext `Warehouse` for stable physical places.

Use `Three PL Container` for movable handling units.

The operational identity is:

`Location + Container + Item/SKU + Quantity`

Example:

- Location: `A-01-R01-S02-B03`
- Container: `BOX-ALPHA-001`
- Item: `ALPHA-SKU-001`
- Quantity: `10 pcs`

## Outbound Courier Parcels

Client feedback identified a common outbound pattern: many small customer orders are picked at the same time, each order already has a courier label/tracking number, and staff attach each label to the picked product or parcel before final packing.

This should not automatically mean every tracking number must become a permanent warehouse container. The model depends on the physical operation:

- If the courier number is only a shipment reference, keep it as a tracking field on the shipment/outbound document.
- If staff physically create a separate parcel/box for that order, it should be represented as an outbound Handling Unit, for example a short-lived `Courier Parcel`, and then marked `Shipped`/`Closed` when handed to the courier.

Barcode handling rule:

- Standard readable labels should be scanned.
- Non-standard labels should be supported where the scanner/browser library can read the symbology and encoded value.
- Manual entry/search by tracking number must remain available because some courier barcodes, including specific carrier formats, may not scan reliably without custom support or hardware validation.

## Implemented

- Handling Unit DocType exists as `Three PL Container`.
- Container move operation DocType exists as `Three PL Container Move`.
- Container repack operation DocType exists as `Three PL Container Repack`.
- Movement history DocType exists as `Three PL Container Movement`.
- Container fields and statuses are owned by the app DocType/configuration files.
- Demo containers are loaded by `erpnext_3pl.demo.warehouse_data`.
- Demo movement records are loaded for received and putaway containers.
- Demo move operation `MOVE-ALPHA-001` is applied by `erpnext_3pl.warehouse.container_moves`.
- Demo repack operation `REPACK-ALPHA-001` is applied by `erpnext_3pl.warehouse.container_repacks`.
- Inventory snapshots are synchronized from active containers by `erpnext_3pl.sync.inventory_snapshots`.
- Minimal scanner-first container move page exists at `/warehouse/container-move` and applies moves immediately for warehouse roles.
- Aggregated inventory report exists as `3PL Client Inventory Summary`.
- Validation checks required fields, statuses, movement history, and reports in `erpnext_3pl.validation.site`.
- Reports include container references through `3PL Containers`, `3PL Container Moves`, `3PL Container Repacks`, `3PL Container Movements`, and related receiving/inventory reports.

## Not Automated Yet

- Split/merge validation.
- Lifecycle transition buttons and guards.
- Submit-time automation that applies `Three PL Container Move` directly from the ERPNext form.
- Scanner-first UI for repack and picking.

## Client Feedback Wording

Standard ERPNext gives us the core stock operations, but not a full Handling Unit module for 3PL warehouse work. We are implementing Handling Units as `Three PL Container`: a custom layer for boxes, cartons, pallets, barcodes, current location, contents, status, and movement history. This approach lets us stay close to ERPNext stock workflows without modifying core ERPNext logic.
