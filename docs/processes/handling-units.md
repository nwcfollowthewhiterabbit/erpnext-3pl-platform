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

## Implemented

- Handling Unit DocType exists as `Three PL Container`.
- Container move operation DocType exists as `Three PL Container Move`.
- Movement history DocType exists as `Three PL Container Movement`.
- Container fields and statuses are created by `scripts/configure_warehouse_mode.py`.
- Demo containers are loaded by `scripts/load_demo_warehouse_data.py`.
- Demo movement records are loaded for received and putaway containers.
- Demo move operation `MOVE-ALPHA-001` is applied by `scripts/apply_container_moves.py`.
- Validation checks required fields, statuses, movement history, and reports in `scripts/validate_site.py`.
- Reports include container references through `3PL Containers`, `3PL Container Moves`, `3PL Container Movements`, and related receiving/inventory reports.

## Not Automated Yet

- Repack flow, for example two small boxes replaced by one larger box.
- Split/merge validation.
- Lifecycle transition buttons and guards.
- Scanner-first mobile page.
- Submit-time automation that applies `Three PL Container Move` directly from the ERPNext form.
- Automatic inventory snapshot recalculation after every stock or container movement.

## Client Feedback Wording

Standard ERPNext gives us the core stock operations, but not a full Handling Unit module for 3PL warehouse work. We are implementing Handling Units as `Three PL Container`: a custom layer for boxes, cartons, pallets, barcodes, current location, contents, status, and movement history. This approach lets us stay close to ERPNext stock workflows without modifying core ERPNext logic.
