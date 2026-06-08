# Stocktake

## Goal

Record a warehouse count operation for a concrete `location + container + item`.

This covers cycle count / inventory checks where warehouse staff count what is physically present and compare it to the system quantity.

## Current Implemented Behavior

Warehouse users can open:

`/warehouse/stocktake`

The scanner page accepts:

- container / Handling Unit;
- item / SKU;
- counted quantity;
- condition;
- UOM;
- notes.

When the user applies stocktake, the system:

- creates a `Three PL Stocktake` record;
- compares counted quantity to the current container item quantity;
- if there is no difference and condition is `OK`, marks the stocktake as `No Difference`;
- if there is a difference or non-OK condition, updates the container item row;
- creates a linked `Three PL Warehouse Correction`;
- creates a `Three PL Container Movement` row with movement type `Adjusted`;
- links the stocktake to the correction and movement.

## Current Boundary

This is an operational Handling Unit stocktake.

It updates container-level inventory and traceability. It does not yet automatically create ERPNext stock-ledger adjustment Stock Entries.

## Related Reports

- `3PL Stocktakes`
- `3PL Warehouse Corrections`
- `3PL Container Movements`
- `3PL Client Inventory`
