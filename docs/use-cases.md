# 3PL Use Cases And Implementation Coverage

This document describes business use cases, not step-by-step QA test cases.

## Actors

- Client user: customer-side user who works through the client portal.
- Warehouse operator: internal warehouse worker who receives, verifies, moves, picks, and packs goods.
- Warehouse manager: internal manager who can supervise warehouse operations and master data.
- Business owner: owner/admin user with broad ERPNext configuration access.

## Client Use Cases

### Client Creates A Receiving Notice

The client wants to notify the warehouse about an expected inbound shipment before goods arrive.

Main flow:

1. Client logs in to the client portal.
2. Client opens Receiving Notices.
3. Client creates a Receiving Notice for their own customer account.
4. Client adds expected products, client SKUs, and quantities.
5. Client submits or saves the notice.
6. Warehouse team can see the notice in ERPNext Desk and prepare to receive goods.

Expected result:

- The notice is stored in ERPNext.
- The notice is tied to the client.
- The client cannot create notices for another client.

Implementation status: implemented as portal MVP.

Current route:

`/client/receiving-notice`

Current demo user:

`alpha.client@example.test`

### Client Reviews Their Receiving Notices

The client wants to see receiving notices they created or that belong to them.

Main flow:

1. Client logs in to the portal.
2. Client opens Receiving Notices.
3. Client reviews the list of notices linked to their customer account.
4. Client opens a notice to see expected items and current status.

Expected result:

- Client sees only their own receiving notices.
- Client does not use ERPNext Desk for this flow.

Implementation status: partially implemented.

The Web Form list is enabled and permissions are customer-restricted. Dedicated client-facing list/detail UX is not yet custom-built.

### Client Reviews Receiving Discrepancies

The client wants to know whether the warehouse found missing, unexpected, damaged, or quantity-mismatched products.

Main flow:

1. Warehouse records a discrepancy during receiving.
2. Client opens the relevant Receiving Notice.
3. Client sees discrepancy type, item, expected quantity, actual quantity, and notes.
4. Client submits an instruction through the portal when a warehouse decision is needed.

Expected result:

- Discrepancies are stored and can be tracked.
- The client can understand what needs a decision.

Implementation status: implemented as portal MVP.

Discrepancies are modeled on the Receiving Notice and visible internally. Client instructions can be submitted through the portal as a separate instruction record linked to the Receiving Notice.

Current route:

`/client/discrepancy-instruction`

### Client Reviews Inventory

The client wants to see their products and current stock.

Main flow:

1. Client logs in to the portal.
2. Client opens Inventory.
3. Client sees only products and stock owned by their customer account.

Expected result:

- Client does not see another client's products or stock.
- Inventory is based on ERPNext stock data.

Implementation status: implemented as portal MVP.

Client-facing inventory uses `Three PL Inventory Snapshot` records. The current snapshot is generated from the demo receiving/container data and is permission-restricted by customer.

Current route:

`/client/inventory`

### Client Creates Shipment Request

The client wants to request outbound shipment of stored goods.

Main flow:

1. Client logs in to the portal.
2. Client creates a shipment request.
3. Client selects products, quantities, and destination details.
4. Warehouse team receives the request and starts picking.

Expected result:

- Shipment request is stored.
- Warehouse receives an internal Pick List for structured item rows.
- Allocated containers are marked as picking work.

Implementation status: implemented as MVP.

Submitted shipment requests with structured item rows are converted into draft ERPNext Pick Lists by the post-deploy/idempotent shipment sync processor. Full packing, dispatch, carrier tracking, and client-facing shipment tracking remain future work.

Current route:

`/client/shipment-request`

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

Submitted inbound receipts update received quantities, variances, notice status, and auto-generated quantity discrepancies. Manual discrepancy rows are still used for damage, quality issues, and inspection notes.

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

Client shipment requests with structured item rows are converted into draft Pick Lists. The Pick List carries client, shipment request, shipment reference, warehouse, scanned location, and container context. Allocated containers move to `Picking` status and inventory snapshots show them as allocated.

### Warehouse Packs And Ships Goods

The operator wants to pack picked goods and ship them out.

Main flow:

1. Operator moves picked goods into `Packing - 3`.
2. Operator packs products.
3. Operator ships from `Shipping - 3`.
4. Shipping stock movement is recorded.

Expected result:

- Packing and shipping use standard Stock Entry movements.

Implementation status: partially implemented.

Stock Entry types and warehouses exist. Detailed packing units, carrier labels, shipment tracking, and portal shipment status are not implemented yet.

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
| Client portal instead of Desk for clients | Implemented as MVP | Client Receiving Notice Web Form exists. |
| Website User without Desk access | Implemented | Demo client user is `Website User`. |
| Client linked to Customer | Implemented | Demo client user is linked to `Demo Client Alpha`. |
| Client can create Receiving Notice | Implemented | Server validation inserts a notice as client user. |
| Client restricted to own Customer | Implemented | Server validation confirms cross-customer creation is blocked. |
| Product ownership | Implemented | `Item.owner_client`, `Item.client_sku`, `Item.client_product_name`. |
| Business identity is Client + SKU | Implemented in data model | Not yet enforced by unique DB constraint. |
| Receiving Notice required workflow | Implemented as MVP | Inbound receipt Stock Entries require client, Receiving Notice, scanned location, and container context. |
| Receiving Area before storage | Implemented as configured flow | Inbound receipt context is required; final storage is handled by separate putaway movement. |
| Temporary receiving area | Implemented | `Temporary Receiving - 3`. |
| Verification/inspection step | Implemented as MVP | Submitted inbound receipts sync received quantities, variances, notice status, and auto-generated discrepancies. |
| Discrepancy types | Implemented | Missing, unexpected, quantity difference, damaged, quality issue. |
| Client notification for discrepancies | Not implemented | Placeholder email exists only to prevent ERPNext email-account errors. |
| Client instructions for discrepancies | Implemented as MVP | Portal Web Form creates `Three PL Client Instruction` records linked to a Receiving Notice. |
| Dynamic storage locations | Implemented as warehouse hierarchy | Locations are modeled as warehouses. |
| Putaway process | Implemented as Stock Entry flow | Uses standard ERPNext stock movement. |
| Picking from locations | Implemented as MVP | Shipment requests with structured item rows create draft Pick Lists and mark allocated containers as `Picking`. |
| Containers/boxes | Implemented as first model | `Three PL Container`; scanner-first UX not implemented. |
| Barcode/location scan fields | Partially implemented | Fields exist; no dedicated scanner/mobile UI. |
| Client inventory visibility | Implemented as MVP | Portal inventory snapshot exists and is customer-filtered by permissions. |
| Receiving history | Partially implemented | Portal Web Form list exists; dedicated polished history UX is not implemented. |
| Shipment requests | Implemented as MVP | Client portal Web Form creates shipment requests. |
| Shipment status tracking | Implemented as MVP | Shipment request has status; automatic outbound status updates are not implemented. |
| Stay close to standard ERPNext | Implemented | Uses custom fields, custom DocTypes, Web Form, reports, stock entries. |

## Remaining Gaps After MVP

- Polished Pick List execution and scanner-first picking UX.
- Automatic stock-ledger-based inventory snapshot refresh.
- Dedicated client-facing discrepancy detail page.
- Real email notifications after SMTP is configured.
- Scanner-first/mobile warehouse UI.
- Carrier labels and shipment tracking integrations.

## Current Recommended Next Build Step

Build automatic conversion from client shipment request to internal warehouse picking flow.
