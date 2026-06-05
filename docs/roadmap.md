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
- Container references in receiving, putaway, picking, packing, discrepancy, and inventory reporting contexts.

Remaining:

- Agree and import the real location naming scheme.
- Add container movement history.
- Add repack workflow, for example two small boxes replaced by one larger box.
- Add empty / closed / replaced container lifecycle states.
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
