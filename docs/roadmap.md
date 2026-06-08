# ERPNext 3PL Roadmap

## Phase 0 - Infrastructure and Access

Status: done.

- ERPNext v16 is deployed in Docker Swarm.
- Public domain is configured: `https://erpnext.77.237.244.169.sslip.io`.
- HTTPS is enabled through the nginx reverse proxy.
- Repository contains stack, setup scripts, nginx reference config, and process docs.

## Phase 1 - Warehouse-Only Baseline

Status: done.

- ERPNext is configured for warehouse-first use.
- Non-warehouse workspaces are hidden from Desk.
- Warehouse locations are created.
- Client tracking fields are added to Stock Entry and Pick List.
- Inbound Shipment Notice exists for client shipment notifications.
- Demo clients, SKUs, barcodes, ASN, and receiving draft are loaded.
- Demo users are available for testing.

## Phase 2 - Manual Process Validation

Status: in progress.

- Run Receiving flow in UI with demo data.
- Validate client portal Receiving Notice, Inventory, Shipment Request, and Discrepancy Instruction routes.
- Validate customer data isolation with Alpha/Beta demo data.
- Validate Business Owner access to products, warehouses, and UOMs.
- Capture client feedback on missing fields, screen friction, and scanner needs.

## Phase 2.1 - Client-Confirmed MVP Flow Scope

Status: in progress.

Client-confirmed first working scope:

- Roles: implemented.
- Receiving products: implemented as MVP through client Receiving Notice, scanner receiving for expected items, required inbound receipt context, warehouse receiving/verification, received quantity sync, variance calculation, discrepancy records, and stock/container references. Remaining work: unexpected-item scanner flow, damaged/quality inspection capture, and polished workflow actions.
- Location moves: implemented for containers through `Three PL Container Move`, movement history, and scanner-first move page. Remaining work: polished scanner UX and stronger operational guards.
- Sending orders: implemented as MVP through client `Three PL Shipment Request` to draft ERPNext Pick List conversion, scanner picking confirmation, and packing/shipping status sync from submitted Stock Entries. Allocated containers are marked as `Picking`, picked containers become `Picked`, and packed/shipped operations update Shipment Request and container movement history. Scanner pages exist at `/warehouse/picking-confirmation` and `/warehouse/outbound-fulfillment`. Remaining work: carrier labels, shipment tracking, and stronger operational guards.
- Warehouse corrections: implemented as MVP through `Three PL Warehouse Correction`, scanner page `/warehouse/correction`, container item updates, and `Adjusted` movement history. Remaining work: automatic ERPNext stock-ledger adjustment Stock Entries for financial/stock posting.
- Inventory / stocktake: not implemented as a dedicated stocktake flow yet. Current inventory snapshots support visibility, but cycle count / stocktake operations need design and implementation.

Client-confirmed reporting scope:

- Product balance on a selected date for the client: partially implemented through current inventory snapshots; date-based historical balance report remains open.
- Warehouse operation turnover for a selected period for client and warehouse users: open.

Immediate fixes from feedback:

- Keep warehouse location rename disabled for normal warehouse roles; treat renaming as an administrative/setup operation.
- Keep invalid container repack/correction drafts from breaking post-deploy processors; mark them as `Needs Review` instead.

## Phase 3 - Warehouse Locations And Containers

Status: in progress.

Decision captured:

- ERPNext `Warehouse` records model only stable physical locations.
- Boxes / cartons are not warehouse locations.
- Boxes / cartons are modeled as `Three PL Container` records.
- The working model is `location + container + item/SKU + quantity`.
- Real warehouse location tree should be created after naming convention and hierarchy depth are agreed with the client.

Implemented:

- Base warehouse hierarchy for demo receiving, inspection, storage, packing, and shipping.
- `Three PL Container` DocType with client, current location, status, barcode/label context, and item rows.
- Handling Unit fields on `Three PL Container`: container type, parent container, replacement container, last moved timestamp, and lifecycle statuses.
- `Three PL Container Movement` DocType and `3PL Container Movements` report for movement history.
- `Three PL Container Move` operation DocType and `3PL Container Moves` report for explicit move operations.
- `scripts/apply_container_moves.py` processor for applying draft container moves.
- `Three PL Container Repack` operation DocType and `3PL Container Repacks` report for consolidation/repack operations.
- `scripts/apply_container_repacks.py` processor for applying draft repacks.
- Strict repack quantity validation between source containers and target contents.
- `scripts/sync_inventory_snapshots.py` processor for syncing client inventory snapshots from active containers.
- Aggregated inventory report `3PL Client Inventory Summary`.
- Minimal scanner-first receiving page at `/warehouse/receiving` for expected item receipt into temporary receiving.
- Minimal scanner-first container move page at `/warehouse/container-move` with immediate apply for warehouse roles.
- Minimal scanner-first putaway page at `/warehouse/putaway` with immediate apply for warehouse roles and explicit `Putaway` movement history.
- Minimal scanner-first repack page at `/warehouse/repack` for full consolidation of source containers into one target container.
- Minimal scanner-first warehouse correction page at `/warehouse/correction` for wrong quantity, unexpected product, damaged product, quality issue, and hold-for-review cases.
- Container references in receiving, putaway, picking, packing, discrepancy, and inventory reporting contexts.

Remaining:

- Agree and import the real location naming scheme.
- Add ERPNext form submit-time automation for container move operations.
- Add partial split/repack scanner UX and stronger guided quantity editing.
- Add unexpected-item receiving and damaged/quality inspection capture to scanner flow.
- Add stock-ledger posting automation for warehouse corrections after correction-type rules are agreed.
- Add UI actions and validation for empty / closed / replaced container lifecycle transitions.
- Automate inventory snapshot updates from stock and container movements.
- Decide whether mixed client / mixed SKU storage is allowed in one location.

## Phase 4 - Scanner and Mobile Workflow

Status: pending.

- Decide whether first stage uses browser plus USB/Bluetooth barcode scanner or dedicated TSD devices.
- Validate scan behavior in ERPNext forms.
- Decide whether a custom scanner-first page is needed for warehouse operators.
- Define required barcode labels for SKU, warehouse locations, and containers.

## Phase 5 - Multi-Client Stock Model

Status: pending.

- Decide whether client ownership is only document-level metadata or must be enforced in stock balance.
- If enforcement is required, evaluate options:
  - separate warehouses per client;
  - batch-based client ownership;
  - custom stock dimension;
  - custom app logic.

## Phase 6 - Traceability

Status: pending.

- Confirm whether serial numbers are needed.
- Confirm whether batch numbers are needed.
- Confirm whether expiry dates are needed.
- Configure item templates and validation rules accordingly.

## Phase 7 - Integrations

Status: pending.

- Courier and shipping integrations.
- Client shipment notification import.
- Export of receiving/picking/dispatch statuses.
- External reporting or BI needs.
