# Receiving

Goal: receive products from a client notification into a temporary warehouse.

## Demo Records

- Client: `Demo Client Alpha`
- ASN / external reference: `ASN-ALPHA-001`
- Inbound Shipment Notice: search by `ASN-ALPHA-001`
- Container / box: `BOX-ALPHA-001`
- Draft Stock Entry: `MAT-STE-2026-00001`
- Temporary warehouse: `Temporary Receiving - 3`

## Manual Flow

1. Open `Stock > Inbound Shipment Notice`.
2. Open the record with external reference `ASN-ALPHA-001`.
3. Review expected items and quantities.
4. Review the `Discrepancies` section.
5. Open `Stock > Three PL Container` or the `Containers` shortcut.
6. Open `BOX-ALPHA-001` and review the physical box contents.
7. Open `Stock > Stock Entry`.
8. Open draft receiving Stock Entry if available, or create a new one.
9. Confirm:
   - Stock Entry Type: `3PL Inbound Receipt`
   - Client: `Demo Client Alpha`
   - Warehouse Flow: `Inbound Receipt`
   - Target Warehouse: `Temporary Receiving - 3`
   - Scanned Location: `Temporary Receiving - 3`
   - Container / Box: `BOX-ALPHA-001`
10. Compare expected quantities against actual received quantities.
11. Submit the Stock Entry when the received quantities are accepted.

## Required Operating Rule

Inbound stock must go through this path:

`Receiving Notice` -> `Receiving Area` -> `Verification` -> `Putaway` -> `Storage Location`

Do not receive goods directly into final storage locations. During unloading and inspection, the final storage location is usually not known yet.

## Discrepancies

The current model supports:

- missing products;
- unexpected products;
- quantity differences;
- damaged products;
- quality issues.

Record these in the `Discrepancies` table on the Receiving Notice. Status values are used to show whether the issue is still open, the client has been notified, instructions were received, or the discrepancy is resolved.

## Containers / Boxes

Cardboard boxes are represented as `Three PL Container` records.

Use a container when staff need to identify the physical box first and then inspect products inside it. The container can be linked to the Receiving Notice, current warehouse location, stock entry rows, and later picking/packing records.

## Notes

The demo receiving draft intentionally has `SKU-ALPHA-002` received as `24` while the notice expects `25`. Use that variance to discuss comparison handling.
