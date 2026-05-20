# Picking / Pick List

Goal: create a pick list and collect stock from warehouse locations.

## Manual Flow

1. Open `Stock > Pick List`.
2. Create a new Pick List.
3. Set:
   - Client: relevant client
   - Shipment Reference: external dispatch/order reference
4. Add items to pick.
5. Use warehouse locations from the item rows.
6. Fill `Scanned Location` for each pick row after scanning the location barcode.
7. Save the Pick List.

## Notes

Standard ERPNext Pick List behavior can be used for item allocation. The custom fields add client and scanned-location context without replacing the standard logic.

