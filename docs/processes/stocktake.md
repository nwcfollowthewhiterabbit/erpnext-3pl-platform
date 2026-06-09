# Stocktake

## Goal

Record a warehouse count operation for a concrete `location + container + item`, optionally grouped under one stocktake session.

This covers cycle count / inventory checks where warehouse staff count what is physically present and compare it to the system quantity.

## Current Implemented Behavior

Warehouse users can open:

`/warehouse/stocktake`

The scanner page accepts:

- stocktake session reference;
- stocktake session notes;
- container / Handling Unit;
- item / SKU;
- counted quantity;
- condition;
- UOM;
- notes.

When the user applies stocktake, the system:

- creates or reuses a `Three PL Stocktake Session` when a session reference is entered;
- creates a `Three PL Stocktake` record;
- links the stocktake line to the session;
- compares counted quantity to the current container item quantity;
- if there is no difference and condition is `OK`, marks the stocktake as `No Difference`;
- if there is a difference or non-OK condition, updates the container item row;
- creates a linked `Three PL Warehouse Correction`;
- creates a `Three PL Container Movement` row with movement type `Adjusted`;
- links the stocktake to the correction and movement.
- posts the linked warehouse correction to ERPNext stock ledger when the quantity delta can be posted automatically.
- can complete the stocktake session from the scanner page.

## Current Boundary

This is an operational Handling Unit stocktake.

It updates container-level inventory and traceability. Count deltas flow through `Three PL Warehouse Correction`, so positive deltas become `3PL Quantity Gain` Stock Entries and negative deltas become `3PL Quantity Loss` Stock Entries when ERPNext stock ledger permits the posting.

`Three PL Stocktake Session` is the MVP grouping layer for larger counts. It groups many `Three PL Stocktake` lines under one reference and provides session status, location scope, start time, completion time, and notes.

If ERPNext cannot post the stock movement automatically, the linked correction is marked `Needs Review`.

## Related Reports

- `3PL Stocktakes`
- `3PL Stocktake Sessions`
- `3PL Warehouse Corrections`
- `3PL Container Movements`
- `3PL Client Inventory`
