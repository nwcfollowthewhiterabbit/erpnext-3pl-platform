# Picking / Pick List

Goal: create a pick list and collect stock from warehouse locations.

## Manual Flow

1. Open `Stock > Pick List`.
2. Open the Pick List generated from the client Shipment Request, or create one manually if needed.
3. Check:
   - Client: relevant client
   - Shipment Reference: external dispatch/order reference
   - Shipment Request: linked client request
4. Review item, warehouse, and container rows.
5. Pick products from the listed warehouse locations and containers.
6. Fill or confirm `Scanned Location` for each pick row after scanning the location barcode.
7. Save the Pick List after operational changes.

## Automatic Shipment Request Sync

Submitted client `Three PL Shipment Request` records with structured item rows are converted into draft ERPNext Pick Lists by `scripts/sync_shipment_requests.py`.

The sync:

- allocates from available `Three PL Inventory Snapshot` rows;
- writes client, shipment request, shipment reference, warehouse, scanned location, and container context to the Pick List;
- marks allocated containers as `Picking`;
- records a `Three PL Container Movement` with movement type `Picking`;
- leaves final packing and shipping confirmation for later operational steps.

## Notes

Standard ERPNext Pick List behavior can be used for item allocation. The custom fields add client and scanned-location context without replacing the standard logic.
