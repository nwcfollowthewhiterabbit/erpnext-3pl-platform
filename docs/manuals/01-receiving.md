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
12. The system syncs submitted inbound receipts back to the Receiving Notice:
   - item `Received Qty`;
   - item `Variance Qty`;
   - notice status;
   - auto-generated discrepancy rows for missing, unexpected, or quantity-difference cases.

## Scanner Flow

Warehouse users can use the scanner-first page:

`/warehouse/receiving`

Flow:

1. Scan or enter the Receiving Notice / ASN.
2. Scan or enter the container / Handling Unit.
3. Scan or enter the item code. The item can be expected on the notice or unexpected.
4. Enter accepted received quantity.
5. Confirm receiving location, normally `Temporary Receiving - 3`.
6. Select condition: `OK`, `Damaged`, `Quality Issue`, or `Hold`.
7. Add inspection notes when needed.
8. Click `Submit Receipt`.

Expected result:

- a submitted `Stock Entry` is created with type `3PL Inbound Receipt`;
- the receipt is linked to the Receiving Notice, client, container, and receiving location;
- the container is created or updated as `Received`;
- the container contents are incremented by the accepted quantity;
- a `Three PL Container Movement` row is written with movement type `Received`;
- the Receiving Notice row is updated with received and variance quantities for expected items;
- unexpected items create a discrepancy row;
- damaged and quality issue receipts create discrepancy rows and keep the notice in review.

Submitting or saving the Receiving Notice alone does not create client inventory. The notice is the client's advance notification. Client-facing inventory changes after warehouse receiving creates or updates containers / Handling Units and inventory snapshots are synchronized.

Current boundary:

- photos and final client decisions still belong in the Receiving Notice discrepancy / client instruction workflow;
- warehouse status actions are available at `/warehouse/receiving-review`;
- a dedicated client-facing discrepancy detail page is still future work.

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

Quantity discrepancies can be generated automatically from submitted inbound Stock Entries. Manual discrepancy rows should still be used for damaged products, quality issues, photos/notes, and other inspection details that cannot be inferred from quantity alone.

## Containers / Boxes

Cardboard boxes are represented as `Three PL Container` records.

Use a container when staff need to identify the physical box first and then inspect products inside it. The container can be linked to the Receiving Notice, current warehouse location, stock entry rows, and later picking/packing records.

## Notes

The demo receiving draft intentionally has `SKU-ALPHA-002` received as `24` while the notice expects `25`. Use that variance to discuss comparison handling.
