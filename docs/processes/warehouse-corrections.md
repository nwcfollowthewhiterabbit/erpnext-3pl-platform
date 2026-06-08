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
- links the correction to the movement history row.

## Current Boundary

This is an operational container-level correction.

It updates the 3PL Handling Unit model and traceability history. It does not yet create ERPNext stock-ledger adjustment Stock Entries automatically.

Stock-ledger adjustment automation remains a separate step because the correct ERPNext document depends on the correction type:

- material receipt for positive unexpected quantity;
- material issue for shrinkage/disposal;
- material transfer or hold movement for damaged/quality items;
- manager review for ambiguous cases.

## Related Reports

- `3PL Warehouse Corrections`
- `3PL Container Movements`
- `3PL Containers`
