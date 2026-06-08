# Putaway

## Business Meaning

Putaway is the controlled step after receiving and verification.

It moves a container / Handling Unit from the receiving area into a final storage location.

This is intentionally separate from a generic location move because the client needs the receiving flow to stay visible:

`Receiving Notice` -> `Receiving Area` -> `Verification` -> `Putaway` -> `Storage Location`

## Current Implemented Behavior

Warehouse users can open:

`/warehouse/putaway`

The page accepts:

- container / Handling Unit code;
- target storage location.

When the user applies putaway, the system:

- creates a `Three PL Container Move` operation;
- creates a `Three PL Container Movement` row with movement type `Putaway`;
- updates the container current warehouse;
- changes the container status to `Stored`;
- links the move operation to the movement history row.

Allowed source statuses:

- `Received`
- `In Verification`
- `Ready for Putaway`

## Difference From Container Move

`/warehouse/container-move` is a generic movement between locations.

`/warehouse/putaway` is a receiving-specific movement from temporary receiving / verification into storage.

Both use the same operation and movement-history DocTypes, but putaway writes movement type `Putaway` so reports can distinguish it from regular internal moves.

## Current Limits

- The scanner page updates the container model and movement history.
- The standard ERPNext Stock Entry putaway flow is still used when stock-ledger movement must be posted.
- Automatic stock-ledger posting from the putaway scanner page is not implemented yet.
- Real warehouse location import is still pending client confirmation of naming convention and hierarchy depth.

## Related Docs

- `docs/manuals/02-putaway.md`
- `docs/client-test-guide.md`
- `docs/warehouse-mode.md`
