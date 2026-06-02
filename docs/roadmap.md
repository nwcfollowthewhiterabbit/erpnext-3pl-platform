# ERPNext 3PL Roadmap

## Phase 0 - Infrastructure and Access

Status: done.

- ERPNext v16 is deployed in Docker Swarm.
- Public domain is configured: `https://erptest.exemstsc.world`.
- Let's Encrypt TLS is enabled.
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
- Submit receiving Stock Entry.
- Create and validate Putaway transfer.
- Create Pick List from stocked SKU.
- Validate Packing and Dispatch movements.
- Capture client feedback on missing fields, screen friction, and scanner needs.

## Phase 3 - Scanner and Mobile Workflow

Status: pending.

- Decide whether first stage uses browser plus USB/Bluetooth barcode scanner or dedicated TSD devices.
- Validate scan behavior in ERPNext forms.
- Decide whether a custom scanner-first page is needed for warehouse operators.
- Define required barcode labels for SKU and warehouse locations.

## Phase 4 - Multi-Client Stock Model

Status: pending.

- Decide whether client ownership is only document-level metadata or must be enforced in stock balance.
- If enforcement is required, evaluate options:
  - separate warehouses per client;
  - batch-based client ownership;
  - custom stock dimension;
  - custom app logic.

## Phase 5 - Traceability

Status: pending.

- Confirm whether serial numbers are needed.
- Confirm whether batch numbers are needed.
- Confirm whether expiry dates are needed.
- Configure item templates and validation rules accordingly.

## Phase 6 - Integrations

Status: pending.

- Courier and shipping integrations.
- Client shipment notification import.
- Export of receiving/picking/dispatch statuses.
- External reporting or BI needs.
