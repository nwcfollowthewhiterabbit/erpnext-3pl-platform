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
- Validate restricted client Desk Workspace flows for Receiving Notice, Inventory reports, Shipment Request, Products, and Discrepancy Instructions.
- Validate customer data isolation with Alpha/Beta demo data.
- Validate Business Owner access to products, warehouses, and UOMs.
- Capture client feedback on missing fields, screen friction, and scanner needs.

## Phase 2.1 - Client-Confirmed MVP Flow Scope

Status: in progress.

Focused readiness table: `docs/client-mvp-scope-status.md`.

Client-confirmed first working scope:

- Roles: implemented.
- Receiving products: implemented as MVP through client Receiving Notice in the restricted `3PL Client` Workspace, scanner receiving for expected and unexpected items, condition capture for damaged/quality issues, required inbound receipt context, warehouse receiving/verification, received quantity sync, variance calculation, discrepancy records, stock/container references, and warehouse review actions at `/warehouse/receiving-review`.
- Location moves: implemented for containers through `Three PL Container Move`, movement history, and scanner-first move page. Remaining work: polished scanner UX and stronger operational guards.
- Sending orders: implemented as MVP through client `Three PL Shipment Request` in the restricted `3PL Client` Workspace to draft ERPNext Pick List conversion, scanner picking confirmation, packing/shipping status sync from submitted Stock Entries, and warehouse shipment review actions at `/warehouse/shipment-review`. Automatic allocation is whole-container only: partial picks from a larger container require a split/repack into a matching container first. Allocated containers are marked as `Picking`, picked containers become `Picked`, and packed/shipped operations update Shipment Request and container movement history. Scanner pages exist at `/warehouse/picking-confirmation` and `/warehouse/outbound-fulfillment`. Remaining work: quantity-level reservation/splitting, carrier labels, external tracking integrations, and stronger operational guards.
- Warehouse corrections: implemented as MVP through `Three PL Warehouse Correction`, scanner page `/warehouse/correction`, container item updates, `Adjusted` movement history, automatic ERPNext Stock Entry posting for clear quantity deltas, manager review queue at `/warehouse/correction-review`, and review metadata for manager decisions. Remaining work: richer multi-step approval workflow if required.
- Inventory / stocktake: implemented as MVP through `Three PL Stocktake Session`, `Three PL Stocktake`, scanner page `/warehouse/stocktake`, counted-vs-system delta, linked correction, `Adjusted` movement history, and correction stock posting where ERPNext ledger permits it. Remaining work: richer large-count assignment/review UX.

Client-confirmed reporting scope:

- Product balance on a selected date for the client: implemented as MVP through daily `Three PL Inventory Balance Snapshot` rows and report `3PL Inventory Balance By Date`. History starts from the day snapshots are generated.
- Warehouse operation turnover for a selected period for client and warehouse users: implemented as MVP through container movement history and report `3PL Warehouse Operation Turnover`.

Immediate fixes from feedback:

- Keep warehouse location rename disabled for normal warehouse roles; treat renaming as an administrative/setup operation.
- Keep invalid container repack/correction drafts from breaking post-deploy processors; mark them as `Needs Review` instead.
- Execute the live-flow reliability backlog so primary MVP actions update the next operational document immediately, without manual processor calls. See `docs/processes/live-flow-reliability-backlog.md`.

## Phase 2.2 - Live Flow Reliability

Status: done for MVP live flows.

Detailed backlog: `docs/processes/live-flow-reliability-backlog.md`.

Goal:

- Make every primary MVP user action produce its expected operational result immediately in the UI.
- Keep batch processors as recovery and reconciliation tools, not as a normal required step for client or warehouse users.
- Split test coverage into deployment, client Desk, and warehouse operation packs.

Queued work:

- Shipment Request save immediately creates or updates the warehouse Pick List.
- Product Import is kept as a post-MVP1 roadmap/admin capability, not as a required MVP1 client flow.
- Standard Stock Entry submit immediately syncs inbound receipt, packing, and shipping results.
- Standard Pick List picked quantity updates immediately sync container statuses and movement history.
- Validation tests include live-flow checks that do not call the sync processors manually.

Remaining boundary:

- Decide after MVP1 whether bulk product import should be exposed to clients, kept admin-only, or staged through warehouse review.
- Keep the server-side route/landing consistency guard in backlog. Add it only if manual testing shows users frequently land in the wrong workspace after login/bookmarks. Do not reintroduce nginx business redirects for this.

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
- `erpnext_3pl.warehouse.container_moves` processor for applying draft container moves.
- `Three PL Container Repack` operation DocType and `3PL Container Repacks` report for consolidation/repack operations.
- `erpnext_3pl.warehouse.container_repacks` processor for applying draft repacks.
- Strict repack quantity validation between source containers and target contents.
- `erpnext_3pl.sync.inventory_snapshots` processor for syncing client inventory snapshots from active containers.
- `erpnext_3pl.sync.inventory_balance_snapshots` processor for storing daily historical inventory balance rows.
- Aggregated inventory report `3PL Client Inventory Summary`.
- Date-based inventory report `3PL Inventory Balance By Date`.
- Warehouse operations turnover report `3PL Warehouse Operation Turnover`.
- Minimal scanner-first receiving page at `/warehouse/receiving` for expected item receipt, unexpected item capture, and damage/quality issue capture into temporary receiving.
- Minimal scanner-first container move page at `/warehouse/container-move` with immediate apply for warehouse roles.
- Minimal scanner-first putaway page at `/warehouse/putaway` with immediate apply for warehouse roles and explicit `Putaway` movement history.
- Minimal scanner-first repack page at `/warehouse/repack` for full consolidation and partial split from one source container into one target container.
- Minimal scanner-first warehouse correction page at `/warehouse/correction` for wrong quantity, unexpected product, damaged product, quality issue, and hold-for-review cases.
- Minimal scanner-first stocktake page at `/warehouse/stocktake` for cycle count by container and SKU.
- `erpnext_3pl.warehouse.warehouse_corrections` processor for posting clear correction quantity deltas into ERPNext Stock Entry.
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

## Stage MVP2 - Client Product Card Management

Status: MVP2 base implemented for product cards and export. Controlled product import is kept outside MVP1 as a post-MVP1 roadmap item.

Client-confirmed future requirement:

- Clients should create new product cards themselves. Base restricted Desk flow is implemented through `Three PL Client Product`.
- Clients should update existing product cards themselves. Base restricted Desk flow is implemented through `Three PL Client Product`.
- Each product card should support at least:
  - owner client;
  - client SKU;
  - product name / description;
  - unit of measure;
  - product photo.
- The business identity should remain `Owner Client + Client SKU`, not global SKU alone.
- The restricted `3PL Client` Workspace provides a safe product management flow without giving clients unrestricted Desk access.
- Excel-compatible export is available for product maintenance. Bulk import is kept as a post-MVP1/admin capability.

Implementation direction:

- Build this on top of standard ERPNext `Item`.
- Keep custom ownership fields (`owner_client`, `client_sku`, `client_product_name`) as the 3PL layer.
- Use restricted ERPNext Desk forms/workspace for client-safe create/update. Client work uses native ERPNext Desk forms and workspace.
- Add validation so a client can only create or update products for their own customer account. Base server validation implemented.
- Keep export templates/reporting as needed after manual testing; bulk import remains post-MVP1.
- Store product photos using ERPNext file attachments or item image fields.
- Record client product changes in `Three PL Client Product Change Log`.

Open design questions:

- Exact final required product fields for the client's operational catalog.
- Whether product approval by warehouse/admin is needed before the item becomes usable.
- Whether clients may reactivate inactive products themselves.
- Whether product imports should keep creating products immediately or be staged for warehouse/admin review.

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
