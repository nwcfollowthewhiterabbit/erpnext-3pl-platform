# Putaway

Goal: move received products from temporary receiving into warehouse locations.

## Prerequisite

Submit the receiving Stock Entry first. ERPNext needs posted incoming stock before it can validate a transfer out of `Temporary Receiving - 3`.

## Manual Flow

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Put Away`.
4. Confirm Purpose is `Material Transfer`.
5. Set:
   - Client: `Demo Client Alpha`
   - Inbound Shipment Notice: the notice for `ASN-ALPHA-001`
   - Warehouse Flow: `Put Away`
6. Add item rows:
   - Source Warehouse: `Temporary Receiving - 3`
   - Target Warehouse: `Aisle A - 3`, `Aisle B - 3`, or `Overflow - 3`
   - Scanned Location: the target location scanned by the operator
7. Save and submit.

## Scanner Behavior

Warehouse users can use the scanner-first page:

`/warehouse/putaway`

Flow:

1. Scan or enter the container / Handling Unit code.
2. Scan or enter the final storage location.
3. Click `Apply Putaway`.

Expected result:

- a `Three PL Container Move` operation is created and marked `Applied`;
- a `Three PL Container Movement` history row is written with movement type `Putaway`;
- the container status becomes `Stored`;
- the container current warehouse becomes the scanned storage location;
- the client-facing Inventory page is updated from the stored container snapshot.

The page accepts containers in `Received`, `In Verification`, or `Ready for Putaway` status. It is intentionally separate from the generic `/warehouse/container-move` page so the receiving-to-storage step remains visible in history.
