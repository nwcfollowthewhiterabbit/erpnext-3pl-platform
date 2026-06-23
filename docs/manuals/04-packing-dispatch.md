# Packing and Dispatch

Goal: move picked products through packing and out of the warehouse.

## Packing

Scanner route:

`/warehouse/outbound-fulfillment`

Scanner-first flow:

1. Open the scanner route.
2. Scan or enter Shipment Request / Reference.
3. Scan or enter Container / HU.
4. Select `Packing`.
5. Submit Operation.

The page creates and submits a `3PL Packing` Stock Entry, then updates the linked Shipment Request, container status, and movement history.

Manual fallback:

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Packing`.
4. Purpose should show `Material Transfer` automatically. It is read-only and should not be edited manually.
5. Move products from storage/picking location to `Packing - 3`.
6. Set:
   - Client
   - Shipment Request
   - Shipment Reference
   - Warehouse Flow: `Packing`
   - Container / Box
7. Save and submit.

After submit, `erpnext_3pl.sync.outbound_fulfillment` updates the linked Shipment Request to `Packed`, marks referenced containers as `Packed`, and creates `Three PL Container Movement` history.

## Dispatch

Scanner-first flow:

1. Open `/warehouse/outbound-fulfillment`.
2. Scan or enter Shipment Request / Reference.
3. Scan or enter Container / HU.
4. Select `Shipping`.
5. Submit Operation.

The page creates and submits a `3PL Shipping` Stock Entry, then updates the linked Shipment Request, container status, and movement history.

Manual fallback:

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Shipping`.
4. Purpose should show `Material Issue` automatically. It is read-only and should not be edited manually.
5. Issue products from the final dispatch/packing warehouse.
6. Set:
   - Client
   - Shipment Request
   - Shipment Reference
   - Warehouse Flow: `Shipping`
   - Container / Box
7. Submit after products are handed over for dispatch.

After submit, `erpnext_3pl.sync.outbound_fulfillment` updates the linked Shipment Request to `Shipped`, marks referenced containers as `Shipped`, and creates `Three PL Container Movement` history.

## Shipment Review

Warehouse users can open:

`/warehouse/shipment-review`

The page lists active client shipment requests and lets the warehouse mark them as `Accepted`, `Closed`, or `Cancelled`. Packing and shipping operations still update `Packed` and `Shipped` statuses from submitted Stock Entries.

## Future Extension

Dispatch can later be connected to courier/shipping systems. For now it is represented as a confirmed ERPNext Stock Entry plus custom shipment/container status sync.

### Courier Parcel / Tracking Label Flow

Client feedback: some outbound orders are physically assembled as one parcel per customer order. The courier label is already known when the client enters the order, and warehouse staff may attach the label to the picked product before final packing/dispatch.

Design direction for a later phase:

- If the parcel is only an external tracking reference, store it as a tracking / courier reference on the Shipment Request or outbound operation.
- If the warehouse physically creates a parcel/box per order, model it as a short-lived outbound Handling Unit, for example a `Courier Parcel`, linked to the Shipment Request and closed after shipping.
- Do not require every courier label to scan successfully. The UX should be scan-first with manual entry/search fallback.
- Non-standard courier barcodes can often be supported, but only after testing real labels from each courier. If the scanner/browser library cannot read a specific symbology or encoded value, staff must still be able to type the tracking number manually.
