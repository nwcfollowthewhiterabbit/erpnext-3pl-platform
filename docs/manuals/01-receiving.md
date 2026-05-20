# Receiving

Goal: receive products from a client notification into a temporary warehouse.

## Demo Records

- Client: `Demo Client Alpha`
- ASN / external reference: `ASN-ALPHA-001`
- Inbound Shipment Notice: search by `ASN-ALPHA-001`
- Draft Stock Entry: `MAT-STE-2026-00001`
- Temporary warehouse: `Temporary Receiving - 3`

## Manual Flow

1. Open `Stock > Inbound Shipment Notice`.
2. Open the record with external reference `ASN-ALPHA-001`.
3. Review expected items and quantities.
4. Open `Stock > Stock Entry`.
5. Open draft `MAT-STE-2026-00001`.
6. Confirm:
   - Stock Entry Type: `3PL Inbound Receipt`
   - Client: `Demo Client Alpha`
   - Warehouse Flow: `Inbound Receipt`
   - Target Warehouse: `Temporary Receiving - 3`
   - Scanned Location: `Temporary Receiving - 3`
7. Compare expected quantities against actual received quantities.
8. Submit the Stock Entry when the received quantities are accepted.

## Notes

The demo receiving draft intentionally has `SKU-ALPHA-002` received as `24` while the notice expects `25`. Use that variance to discuss comparison handling.

