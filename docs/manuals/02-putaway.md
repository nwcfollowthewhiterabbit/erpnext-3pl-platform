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

At this stage, scanner input is represented by the `Scanned Location` field. A USB/Bluetooth barcode scanner should work as keyboard input in the browser.

