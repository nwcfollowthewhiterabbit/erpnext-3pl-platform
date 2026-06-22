# 3PL Use Cases And Implementation Coverage

This document describes business use cases, not step-by-step QA test cases.

## Actors

- Client user: customer-side restricted ERPNext Desk user who works through the `3PL Client` Workspace.
- Warehouse operator: internal warehouse worker who receives, verifies, moves, picks, and packs goods.
- Warehouse manager: internal manager who can supervise warehouse operations and master data.
- Business owner: owner/admin user with broad ERPNext configuration access.

## Client Use Cases

### Client Creates A Receiving Notice

The client wants to notify the warehouse about an expected inbound shipment before goods arrive.

Main flow:

1. Client logs in to ERPNext Desk.
2. Client opens Receiving Notices.
3. Client creates a Receiving Notice for their own customer account.
4. Client adds expected products, client SKUs, and quantities.
5. Client submits or saves the notice.
6. Warehouse team can see the notice in ERPNext Desk and prepare to receive goods.

Expected result:

- The notice is stored in ERPNext.
- The notice is tied to the client.
- The client cannot create notices for another client.

Implementation status: implemented as Desk-native MVP.

Current entry point:

`/desk/3pl-client`

Current demo user:

`alpha.client@example.test`

### Client Reviews Their Receiving Notices

The client wants to see receiving notices they created or that belong to them.

Main flow:

1. Client logs in to ERPNext Desk.
2. Client opens Receiving Notices.
3. Client reviews the list of notices linked to their customer account.
4. Client opens a notice to see expected items and current status.

Expected result:

- Client sees only their own receiving notices.
- Client uses only the restricted `3PL Client` Workspace, not unrestricted ERPNext Desk.

Implementation status: implemented as Desk-native MVP.

Client access is customer-restricted through User Permission, DocType permissions, and server-side customer/data guards. MVP1 client work uses the restricted ERPNext Desk workspace. A route/landing consistency guard is backlog-only unless manual testing proves it is needed.

### Client Reviews Receiving Discrepancies

The client wants to know whether the warehouse found missing, unexpected, damaged, or quantity-mismatched products.

Main flow:

1. Warehouse records a discrepancy during receiving.
2. Client opens the relevant Receiving Notice.
3. Client sees discrepancy type, item, expected quantity, actual quantity, and notes.
4. Client submits an instruction from the restricted client Workspace when a warehouse decision is needed.

Expected result:

- Discrepancies are stored and can be tracked.
- The client can understand what needs a decision.

Implementation status: implemented as Desk-native MVP.

Discrepancies are modeled on the Receiving Notice and visible internally. Client instructions are submitted as separate customer-scoped instruction records linked to the Receiving Notice.

Current entry point:

`/desk/3pl-client`

### Client Reviews Inventory

The client wants to see their products and current stock.

Main flow:

1. Client logs in to ERPNext Desk.
2. Client opens Inventory.
3. Client sees only products and stock owned by their customer account.

Expected result:

- Client does not see another client's products or stock.
- Inventory is based on ERPNext stock data.

Implementation status: implemented as Desk-native MVP.

Client-facing inventory uses `Three PL Inventory Snapshot` records. The current snapshot is generated from the demo receiving/container data and is permission-restricted by customer.

Current entry point:

`/desk/3pl-client`

### Client Reviews Product Balance On A Date

The client wants to see product balance as of a selected calendar day.

Main flow:

1. System synchronizes current inventory snapshots.
2. System stores daily inventory balance rows.
3. Warehouse or management user opens `3PL Inventory Balance By Date`.
4. User filters by date, client, product, status, location, or container.

Expected result:

- Balance rows are stable for the captured day.
- Client-owned stock remains separated by customer.
- Historical reporting does not depend on the mutable current snapshot only.

Implementation status: implemented as MVP.

History is stored in `Three PL Inventory Balance Snapshot`. The report starts producing useful historical data from the first day the processor runs; it does not backfill dates before the system started capturing snapshots.

### Client Creates Shipment Request

The client wants to request outbound shipment of stored goods.

Main flow:

1. Client logs in to ERPNext Desk.
2. Client creates a shipment request.
3. Client selects products, quantities, and destination details.
4. Warehouse team receives the request and starts picking.

Expected result:

- Shipment request is stored.
- Warehouse receives an internal Pick List for structured item rows.
- Allocated containers are marked as picking work.

Implementation status: implemented as MVP.

Submitted shipment requests with structured item rows are converted into draft ERPNext Pick Lists by the immediate shipment sync hook and the idempotent recovery processor. Packing and dispatch are implemented as MVP through `3PL Packing` and `3PL Shipping` Stock Entries, and client-facing status is available through the restricted `3PL Client` Workspace. Carrier labels, courier integrations, and polished external tracking remain future work.

Current entry point:

`/desk/3pl-client`

## Warehouse Use Cases

### Warehouse Receives Goods Against A Receiving Notice

The operator wants to receive arriving goods based on a client Receiving Notice.

Main flow:

1. Operator opens the Receiving Notice.
2. Operator unloads goods into the receiving area.
3. Operator creates or opens a Stock Entry using `3PL Inbound Receipt`.
4. Operator records actual received quantities.
5. Goods are received into `Temporary Receiving - 3`.

Expected result:

- Goods are not received directly into final storage locations.
- Actual receiving is linked to client and Receiving Notice.

Implementation status: implemented as ERPNext Desk flow.

### Warehouse Identifies A Box Or Container

The operator wants to identify a physical box first, then inspect the products inside it.

Main flow:

1. Operator scans or opens a container/box record.
2. Operator links the box to the client and Receiving Notice.
3. Operator records products and quantities inside the box.
4. Operator keeps the box in receiving until verification is done.

Expected result:

- Box/container is tracked separately from products.
- The box has a current warehouse location.
- The box can be referenced on receiving, putaway, picking, and packing documents.

Implementation status: implemented as first ERPNext custom DocType model.

Current DocType:

`Three PL Container`

Demo record:

`BOX-ALPHA-001`

### Warehouse Compares Expected And Actual Receiving

The operator wants to compare the Receiving Notice against actual received goods.

Main flow:

1. Operator reviews expected products and quantities.
2. Operator records actual quantities.
3. Operator identifies missing, unexpected, damaged, or mismatched products.
4. Operator records discrepancies on the Receiving Notice.
5. Manager or client decides what to do with unresolved discrepancies.

Expected result:

- Quantity differences and quality issues are stored.
- Discrepancy status can be tracked.

Implementation status: implemented as MVP.

Submitted inbound receipts update received quantities, variances, notice status, and auto-generated discrepancies. A scanner-first receiving page exists at `/warehouse/receiving` for expected items, unexpected items, and damaged/quality issue capture.

### Warehouse Puts Goods Away Into Storage

The operator wants to move verified goods from receiving into final storage locations.

Main flow:

1. Operator confirms receiving/verification is done.
2. Operator creates a Stock Entry using `3PL Put Away`.
3. Operator moves goods from `Temporary Receiving - 3` to a storage location.
4. Operator records scanned location and container where applicable.

Expected result:

- Stock is moved through standard ERPNext stock logic.
- Final location is assigned after receiving and verification.

Implementation status: implemented as ERPNext Desk flow.

### Warehouse Picks Goods For Outbound Work

The operator wants to pick products from storage locations.

Main flow:

1. Operator opens or creates a Pick List.
2. Operator picks products from locations.
3. Operator records scanned location and container where applicable.
4. Picked goods move toward packing.

Expected result:

- Picking uses ERPNext Pick List.
- Location/container context can be recorded.

Implementation status: implemented as MVP.

Client shipment requests with structured item rows are converted into draft Pick Lists. The Pick List carries client, shipment request, shipment reference, warehouse, scanned location, and container context. Automatic MVP allocation is whole-container only: if a request needs less than the quantity currently held in a container, warehouse users must split or repack the goods into a matching container before allocation. Allocated containers move to `Picking` status and inventory snapshots show the whole allocated container as allocated. A scanner-first confirmation page exists at `/warehouse/picking-confirmation`.

### Warehouse Packs And Ships Goods

The operator wants to pack picked goods and ship them out.

Main flow:

1. Operator moves picked goods into `Packing - 3`.
2. Operator packs products.
3. Operator ships from `Shipping - 3`.
4. Shipping stock movement is recorded.

Expected result:

- Packing and shipping use standard Stock Entry movements.
- Shipment Request status is updated from submitted Stock Entries.
- Container movement history records packed and shipped events.

Implementation status: implemented as MVP.

Submitted `3PL Packing` and `3PL Shipping` Stock Entries with shipment context update the Shipment Request, referenced containers, and container movement history. A scanner-first page exists at `/warehouse/outbound-fulfillment` for warehouse roles. Detailed packing units, carrier labels, courier integrations, and polished shipment tracking are not implemented yet.

### Warehouse Reviews Operation Turnover

The manager wants to review warehouse operations over a period.

Main flow:

1. Warehouse operations create movement history rows.
2. Manager opens `3PL Warehouse Operation Turnover`.
3. Manager filters by operation date, client, operation type, location, or container.

Expected result:

- Receiving, putaway, moves, repacks, corrections, stocktakes, picking, packing, and shipping are visible in one operations report.
- The report is based on `Three PL Container Movement`, not on free-text notes.

Implementation status: implemented as MVP.

## Management Use Cases

### Manager Maintains Products And Warehouses

The manager or business owner wants to configure products, warehouses, UOMs, and warehouse locations.

Main flow:

1. Manager or owner logs in to ERPNext Desk.
2. User creates or edits products.
3. User assigns product ownership with Owner Client and Client SKU.
4. User creates or edits warehouse locations.

Expected result:

- Product business identity is `Owner Client + Client SKU`.
- ERPNext item code can remain readable and unique.

Implementation status: implemented for owner/admin, partially implemented for manager.

The business owner has broad system rights. The warehouse manager is operationally scoped and does not have unrestricted system-admin rights.

## Implementation Coverage Summary

| Requirement | Status | Notes |
| --- | --- | --- |
| ERPNext v16 clean install | Implemented | Deployed on prod and validated. |
| Warehouse-only internal Desk | Implemented | Non-warehouse modules hidden via module profile/workspaces. |
| Restricted client Desk instead of custom portal | Implemented as MVP | Demo client user is a System User with `3PL Client` role, `3PL Client Only` module profile, default `3PL Client` Workspace, Customer User Permission, and server-side customer/status guards. |
| Native ERPNext Desk client surface | Implemented | Client actions run through restricted ERPNext Desk workspaces and forms. |
| Client linked to Customer | Implemented | Demo client user is linked to `Demo Client Alpha`. |
| Client can create Receiving Notice | Implemented | Client selects active synced products from their product catalog; server validation expands the structured Desk payload into Receiving Notice item rows. |
| Client restricted to own Customer | Implemented | Server validation confirms cross-customer creation is blocked. |
| Product ownership | Implemented | `Item.owner_client`, `Item.client_sku`, `Item.client_product_name`. |
| Business identity is Client + SKU | Implemented in data model | Not yet enforced by unique DB constraint. |
| Receiving Notice required workflow | Implemented as MVP | Client Receiving Notices use structured item rows based on `Three PL Client Product`; inbound receipt Stock Entries require client, Receiving Notice, scanned location, and container context. Scanner receiving exists at `/warehouse/receiving`. |
| Receiving Area before storage | Implemented as configured flow | Inbound receipt context is required; final storage is handled by separate putaway movement. |
| Temporary receiving area | Implemented | `Temporary Receiving - 3`. |
| Verification/inspection step | Implemented as MVP | Submitted inbound receipts sync received quantities, variances, notice status, and auto-generated discrepancies. |
| Discrepancy types | Implemented | Missing, unexpected, quantity difference, damaged, quality issue. |
| Client notification for discrepancies | Not implemented | Placeholder email exists only to prevent ERPNext email-account errors. |
| Client instructions for discrepancies | Implemented as MVP | Restricted client Desk flow creates `Three PL Client Instruction` records linked to a Receiving Notice. |
| Dynamic storage locations | Implemented as warehouse hierarchy | Locations are modeled as warehouses. |
| Putaway process | Implemented as MVP | Uses standard ERPNext Stock Entry flow and a scanner-first container putaway page at `/warehouse/putaway`. |
| Picking from locations | Implemented as MVP with whole-container allocation | Client Shipment Requests use structured product rows from the client catalog, create draft Pick Lists for exact whole-container quantities, and scanner picking confirmation marks containers as `Picked`. Partial picks require a prior split/repack into a matching container. |
| Warehouse corrections | Implemented as MVP | Scanner page `/warehouse/correction` updates container contents/condition and writes `Adjusted` movement history. Clear quantity deltas are posted to ERPNext Stock Entry. |
| Warehouse correction stock posting | Implemented as MVP | Clear quantity deltas create `3PL Quantity Gain` or `3PL Quantity Loss` Stock Entries; blocked postings are marked `Needs Review`. |
| Warehouse correction review | Implemented as MVP | Managers can review `Needs Review` corrections at `/warehouse/correction-review` and report `3PL Corrections Needing Review`. |
| Inventory / stocktake | Implemented as MVP | Scanner page `/warehouse/stocktake` records counted quantity by container/SKU and links deltas to warehouse corrections. |
| Containers/boxes | Implemented as first model | `Three PL Container`; scanner-first pages exist for receiving, container moves, putaway, correction, repack, picking confirmation, and outbound fulfillment. |
| Barcode/location scan fields | Partially implemented | Scanner pages exist for receiving, container moves, putaway, correction, stocktake, repack, picking, and outbound fulfillment. Multi-item partial split guidance still needs polish. |
| Client inventory visibility | Implemented as MVP | Inventory snapshot/report access is customer-filtered by permissions and Workspace/report roles. |
| Product balance on date | Implemented as MVP | Daily `Three PL Inventory Balance Snapshot` rows and `3PL Inventory Balance By Date` report. |
| Warehouse operation turnover | Implemented as MVP | `3PL Warehouse Operation Turnover` report reads movement history. |
| Receiving history | Implemented as MVP | Client can review customer-scoped Receiving Notices through the restricted Workspace. |
| Shipment requests | Implemented as MVP | Restricted client Desk flow creates shipment requests, Pick Lists, and packing/shipping status sync. |
| Shipment status tracking | Implemented as MVP | Shipment Request status updates from submitted packing/shipping Stock Entries and is visible through the restricted `3PL Client` Workspace; carrier tracking integrations remain future work. |
| Stay close to standard ERPNext | Improved | Uses ERPNext Desk, Workspaces, DocTypes, Workflow, reports, permissions, stock entries, and server-side guards. MVP1 uses native ERPNext Desk. |

## Remaining Gaps After MVP

- Richer approval workflow and audit trail for correction stock postings that ERPNext cannot post automatically.
- Grouped stocktake sessions.
- Richer guided quantity editing for multi-item partial repacks.
- Automatic event-based inventory snapshot refresh after every operation.
- Backfill of inventory balance history for dates before daily snapshots were enabled.
- Dedicated client-facing discrepancy detail page.
- Real email notifications after SMTP is configured.
- Scanner-first/mobile warehouse UI.
- Carrier labels and shipment tracking integrations.

## Current Recommended Next Build Step

Build grouped stocktake sessions so multiple container/SKU counts can be managed as one inventory count operation.
