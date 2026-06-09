# Warehouse Corrections

## Goal

Record operational corrections when warehouse staff find that a container does not match the expected state.

Examples:

- wrong quantity in a box;
- unexpected product in a box;
- damaged product;
- quality issue;
- hold for manual review.

## Current Implemented Behavior

Warehouse users can open:

`/warehouse/correction`

The scanner page accepts:

- container / Handling Unit;
- item / SKU;
- actual quantity;
- correction type;
- condition;
- UOM;
- notes.

When the user applies the correction, the system:

- creates a `Three PL Warehouse Correction` record;
- updates the item row in `Three PL Container`;
- adds the item row if the product was unexpected in that container;
- sets the container to `In Verification` when condition is not `OK`;
- creates a `Three PL Container Movement` row with movement type `Adjusted`;
- links the correction to the movement history row;
- creates an ERPNext Stock Entry for quantity deltas when the posting is unambiguous.

## Current Boundary

This is an operational container-level correction.

It updates the 3PL Handling Unit model and traceability history. Quantity increases are posted as `3PL Quantity Gain` Material Receipt. Quantity decreases are posted as `3PL Quantity Loss` Material Issue when ERPNext stock ledger allows the issue.

If ERPNext blocks the stock posting, for example because ledger stock is insufficient for a Material Issue, the correction is kept operationally applied but its `Stock Posting Status` becomes `Needs Review`.

Warehouse managers can review these records from:

`/warehouse/correction-review`

The review page shows corrections where stock posting needs a decision. A manager can:

- reset the correction to `Pending` for the next processor retry;
- mark the correction as `Not Required` when no ERPNext stock posting should be created.

Still requiring manager review:

- material transfer or hold movement for damaged/quality items;
- ambiguous correction types where physical and financial stock treatment must be decided.

## Related Reports

- `3PL Warehouse Corrections`
- `3PL Corrections Needing Review`
- `3PL Container Movements`
- `3PL Containers`
