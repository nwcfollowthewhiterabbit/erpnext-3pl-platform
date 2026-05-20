# Warehouse Mode

This ERPNext instance is configured for an initial 3PL warehouse workflow without external integrations.

## Visible Desk Areas

Only the operational areas are visible by default:

- Home
- Stock
- Users

Accounting, Buying, Selling, CRM, Manufacturing, Projects, Support, Website, and integrations are hidden from the main Desk navigation. They are not uninstalled, because ERPNext depends on parts of the standard app internally.

## Warehouse Structure

- `Receiving Area - 3`
- `Temporary Receiving - 3`
- `Inspection and Comparison - 3`
- `Storage Locations - 3`
- `Aisle A - 3`
- `Aisle B - 3`
- `Overflow - 3`
- `Packing - 3`
- `Shipping - 3`

## Receiving Flow

1. Create an `Inbound Shipment Notice` for the client notification.
2. Receive actual products with a `Stock Entry` using `3PL Inbound Receipt`.
3. Put received products into `Temporary Receiving - 3`.
4. Compare expected vs actual quantities against the notice.
5. Move products into final locations with `3PL Put Away`.

Demo data includes a draft receiving Stock Entry. Submit that receiving entry before creating the putaway transfer, because ERPNext needs posted incoming stock before it can validate an outgoing transfer.

## Picking and Shipping Flow

1. Create a `Pick List`.
2. Pick from warehouse locations.
3. Use the custom `Scanned Location` field when scanning location + product.
4. Move picked stock to `Packing - 3`.
5. Ship from `Shipping - 3` using `3PL Shipping`.

## Client Tracking

Custom fields were added to:

- `Stock Entry`: `Client`, `Inbound Shipment Notice`, `Warehouse Flow`, `Scanned Location`
- `Stock Entry Detail`: `Scanned Location`
- `Pick List`: `Client`, `Shipment Reference`
- `Pick List Item`: `Scanned Location`

This is intentionally a lightweight starting point. It records client ownership on warehouse documents, but does not yet enforce client-level stock segregation in the stock ledger.
