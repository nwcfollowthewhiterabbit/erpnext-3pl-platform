# Packing and Dispatch

Goal: move picked products through packing and out of the warehouse.

## Packing

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Packing`.
4. Use Purpose: `Material Transfer`.
5. Move products from storage/picking location to `Packing - 3`.
6. Set Client and Shipment Reference context where available.
7. Save and submit.

## Dispatch

1. Open `Stock > Stock Entry`.
2. Create a new Stock Entry.
3. Select Stock Entry Type: `3PL Shipping`.
4. Use Purpose: `Material Issue`.
5. Issue products from `Shipping - 3`.
6. Submit after products are handed over for dispatch.

## Future Extension

Dispatch can later be connected to courier/shipping systems. For now it is represented as a stock issue from the shipping warehouse.

