# Warehouse Mode

This ERPNext instance is configured for an initial 3PL warehouse workflow without external integrations.

## Visible Desk Areas

Only the operational areas are visible by default:

- Home
- Stock
- Users

Accounting, Buying, Selling, CRM, Manufacturing, Projects, Support, Website, and integrations are hidden from the main Desk navigation. They are not uninstalled, because ERPNext depends on parts of the standard app internally.

## Warehouse Structure

ERPNext `Warehouse` records are used for stable physical warehouse locations only. They should describe places that exist independently from the stock currently inside them:

- receiving areas;
- inspection areas;
- zones;
- aisles;
- racks;
- shelves;
- bins / cells.

Current seed structure:

- `Receiving Area - 3`
- `Temporary Receiving - 3`
- `Inspection and Comparison - 3`
- `Storage Locations - 3`
- `Aisle A - 3`
- `Aisle B - 3`
- `Overflow - 3`
- `Packing - 3`
- `Shipping - 3`

### Locations vs Containers

The current architecture separates physical locations from boxes / cartons:

- Location means where goods are stored.
- Container / box means what physical handling unit holds the goods.
- Item / SKU means what product is inside.
- Quantity means how much product is inside.

Boxes must not be modeled as ERPNext `Warehouse` locations. A box is transient: it can be replaced, merged, repacked, emptied, or closed. ERPNext warehouse locations cannot be freely deleted after stock transactions, so using boxes as warehouse locations would create an unstable and hard-to-maintain warehouse tree.

Boxes are modeled as `Three PL Container` records instead. A container has an owner client, current warehouse location, status, optional barcode / label, and item rows. This lets warehouse staff identify a physical box first, then inspect or move products inside it.

In WMS terminology, `Three PL Container` is the project-level Handling Unit model. Standard ERPNext does not provide a complete 3PL Handling Unit workflow out of the box, so this repository adds that layer while keeping ERPNext stock movements, warehouses, items, pick lists, and stock entries as the operational base.

Example:

- `Aisle A / Rack 01 / Shelf 02 / Bin 03` is a warehouse location.
- `BOX-ALPHA-001` is a container currently stored in that location.
- `ALPHA-SKU-001` is an item inside the container.
- `10 pcs` is the quantity.

If two small boxes are later replaced by one larger box, the location stays the same. The old containers should be marked empty / closed / replaced, and the new container should receive the consolidated contents. That workflow is not fully automated yet.

### Location Naming Convention

Before creating the real warehouse tree, agree the naming convention and required detail level. Recommended format:

`ZONE-AISLE-RACK-SHELF-BIN`

Examples:

- `A-01-R01-S02-B03`
- `A-01-R01-S02-B04`
- `B-02-R03-S01-B01`

The client can start preparing the warehouse location scheme now, but the final import should wait until the naming convention and hierarchy depth are confirmed. Locations that were used in stock transactions should be disabled or archived instead of deleted.

## Receiving Flow

1. Create an `Inbound Shipment Notice` for the client notification.
2. Receive actual products with a `Stock Entry` using `3PL Inbound Receipt`.
3. Put received products into `Temporary Receiving - 3`.
4. Compare expected vs actual quantities against the notice.
5. Move products into final locations with `3PL Put Away`.

Demo data includes a draft receiving Stock Entry. Submit that receiving entry before creating the putaway transfer, because ERPNext needs posted incoming stock before it can validate an outgoing transfer.

## Picking and Shipping Flow

1. Client creates a `Three PL Shipment Request`.
2. The shipment sync processor creates a draft `Pick List` for structured request item rows.
3. Warehouse staff pick from the listed warehouse locations and containers.
4. Use the custom `Scanned Location` field when scanning location + product.
5. Move picked stock to `Packing - 3`.
6. Ship from `Shipping - 3` using `3PL Shipping`.

## Client Tracking

Custom fields were added to:

- `Stock Entry`: `Client`, `Inbound Shipment Notice`, `Warehouse Flow`, `Scanned Location`
- `Stock Entry Detail`: `Scanned Location`
- `Pick List`: `Client`, `Shipment Reference`, `Shipment Request`
- `Pick List Item`: `Scanned Location`

This is intentionally a lightweight starting point. It records client ownership on warehouse documents, but does not yet enforce client-level stock segregation in the stock ledger.

## Current Container Implementation

Implemented:

- `Three PL Container` DocType exists.
- Containers can be linked to owner clients.
- Containers have a type, for example box, carton, pallet, tote, or other.
- Containers have current warehouse location and status.
- Containers have lifecycle statuses: expected, received, verification, putaway-ready, stored, picking, picked, packed, shipped, empty, closed, and replaced.
- Containers can reference a parent container and replacement container.
- Containers have a last moved timestamp field.
- Container item rows can show what is inside the box.
- Container move operations are stored in `Three PL Container Move`.
- Container repack operations are stored in `Three PL Container Repack`.
- Container movement history is stored in `Three PL Container Movement`.
- Draft container moves can be applied by `scripts/apply_container_moves.py`.
- Draft container repacks can be applied by `scripts/apply_container_repacks.py`.
- Inventory snapshots can be synchronized from active containers by `scripts/sync_inventory_snapshots.py`.
- Aggregated inventory is available through `3PL Client Inventory Summary`.
- Minimal scanner-first container move page is available at `/warehouse/container-move` and applies moves immediately for warehouse roles.
- Container links exist in receiving, putaway, picking, packing, and inventory snapshot contexts.
- Reports include container references and movement history where relevant.

Still pending:

- repack workflow, for example two small boxes consolidated into one larger box;
- empty / closed / replaced container lifecycle actions;
- scanner-first UX for scanning location, then container, then item / quantity;
- ERPNext form submit-time or scanner-page automation for move/repack documents;
- automatic inventory snapshot updates from stock movements and container movements;
- import or guided creation of the client's real warehouse location tree.
