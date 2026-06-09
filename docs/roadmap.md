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

Focused readiness table: `docs/client-mvp-scope-status.md`.

Client-confirmed first working scope:

- Roles: implemented.
- Receiving products: implemented as MVP through client Receiving Notice, scanner receiving for expected and unexpected items, condition capture for damaged/quality issues, required inbound receipt context, warehouse receiving/verification, received quantity sync, variance calculation, discrepancy records, stock/container references, warehouse review actions at `/warehouse/receiving-review`, and client discrepancy review at `/client/discrepancies`.
- Location moves: implemented for containers through `Three PL Container Move`, movement history, and scanner-first move page. Remaining work: polished scanner UX and stronger operational guards.
- Sending orders: implemented as MVP through client `Three PL Shipment Request` to draft ERPNext Pick List conversion, scanner picking confirmation, packing/shipping status sync from submitted Stock Entries, warehouse shipment review actions at `/warehouse/shipment-review`, and client shipment tracking at `/client/shipment-tracking`. Allocated containers are marked as `Picking`, picked containers become `Picked`, and packed/shipped operations update Shipment Request and container movement history. Scanner pages exist at `/warehouse/picking-confirmation` and `/warehouse/outbound-fulfillment`. Remaining work: carrier labels, external tracking integrations, and stronger operational guards.
- Warehouse corrections: implemented as MVP through `Three PL Warehouse Correction`, scanner page `/warehouse/correction`, container item updates, `Adjusted` movement history, automatic ERPNext Stock Entry posting for clear quantity deltas, manager review queue at `/warehouse/correction-review`, and review metadata for manager decisions. Remaining work: richer multi-step approval workflow if required.
- Inventory / stocktake: implemented as MVP through `Three PL Stocktake Session`, `Three PL Stocktake`, scanner page `/warehouse/stocktake`, counted-vs-system delta, linked correction, `Adjusted` movement history, and correction stock posting where ERPNext ledger permits it. Remaining work: richer large-count assignment/review UX.

Client-confirmed reporting scope:

- Product balance on a selected date for the client: implemented as MVP through daily `Three PL Inventory Balance Snapshot` rows and report `3PL Inventory Balance By Date`. History starts from the day snapshots are generated.
- Warehouse operation turnover for a selected period for client and warehouse users: implemented as MVP through container movement history and report `3PL Warehouse Operation Turnover`.

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
- `scripts/sync_inventory_balance_snapshots.py` processor for storing daily historical inventory balance rows.
- Aggregated inventory report `3PL Client Inventory Summary`.
- Date-based inventory report `3PL Inventory Balance By Date`.
- Warehouse operations turnover report `3PL Warehouse Operation Turnover`.
- Minimal scanner-first receiving page at `/warehouse/receiving` for expected item receipt, unexpected item capture, and damage/quality issue capture into temporary receiving.
- Minimal scanner-first container move page at `/warehouse/container-move` with immediate apply for warehouse roles.
- Minimal scanner-first putaway page at `/warehouse/putaway` with immediate apply for warehouse roles and explicit `Putaway` movement history.
- Minimal scanner-first repack page at `/warehouse/repack` for full consolidation and partial split from one source container into one target container.
- Minimal scanner-first warehouse correction page at `/warehouse/correction` for wrong quantity, unexpected product, damaged product, quality issue, and hold-for-review cases.
- Minimal scanner-first stocktake page at `/warehouse/stocktake` for cycle count by container and SKU.
- `scripts/apply_warehouse_corrections.py` processor for posting clear correction quantity deltas into ERPNext Stock Entry.
- Manager review page `/warehouse/correction-review` and report `3PL Corrections Needing Review`.
- Container references in receiving, putaway, picking, packing, discrepancy, and inventory reporting contexts.

Remaining:

- Agree and import the real location naming scheme.
- Add ERPNext form submit-time automation for container move operations.
- Add richer guided quantity editing for multi-item partial repacks.
- Add richer guided workflow actions after receiving discrepancies are found.
- Add richer approval workflow and audit trail for correction stock postings that ERPNext marks as `Needs Review`.
- Add richer large-count assignment/review UX for stocktake sessions.
- Add UI actions and validation for empty / closed / replaced container lifecycle transitions.
- Automate inventory snapshot updates immediately after every stock and container movement rather than only through processors.
- Decide whether mixed client / mixed SKU storage is allowed in one location.
- Import real warehouse locations from `docs/templates/warehouse-locations-template.csv` after naming convention is confirmed.

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
