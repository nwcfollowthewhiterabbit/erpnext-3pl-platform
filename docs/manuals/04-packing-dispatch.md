# Packing and Dispatch

Goal: move picked products through packing and out of the warehouse.

## Packing

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Packing`.
4. Use Purpose: `Material Transfer`.
5. Move products from storage/picking location to `Packing - 3`.
6. Set:
   - Client
   - Shipment Request
   - Shipment Reference
   - Warehouse Flow: `Packing`
   - Container / Box
7. Save and submit.

After submit, `scripts/sync_outbound_fulfillment.py` updates the linked Shipment Request to `Packed`, marks referenced containers as `Packed`, and creates `Three PL Container Movement` history.

## Dispatch

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Shipping`.
4. Use Purpose: `Material Issue`.
5. Issue products from the final dispatch/packing warehouse.
6. Set:
   - Client
   - Shipment Request
   - Shipment Reference
   - Warehouse Flow: `Shipping`
   - Container / Box
7. Submit after products are handed over for dispatch.

After submit, `scripts/sync_outbound_fulfillment.py` updates the linked Shipment Request to `Shipped`, marks referenced containers as `Shipped`, and creates `Three PL Container Movement` history.

## Future Extension

Dispatch can later be connected to courier/shipping systems. For now it is represented as a confirmed ERPNext Stock Entry plus custom shipment/container status sync.
