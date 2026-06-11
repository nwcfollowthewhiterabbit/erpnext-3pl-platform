# Client Test Guide

Use this guide for the current ERPNext 3PL test instance.

## URL

`https://erpnext.77.237.244.169.sslip.io`

## Test Accounts

### Warehouse Operator

- Login: `warehouse.demo@example.test`
- Password: `see WAREHOUSE_OPERATOR_PASSWORD in .env`
- Purpose: receiving, stock entries, pick lists, basic warehouse operations.
- Not intended for system setup or master-data administration.

### Warehouse Manager

- Login: `warehouse.manager@example.test`
- Password: `see WAREHOUSE_MANAGER_PASSWORD in .env`
- Purpose: warehouse operations with manager-level stock rights.
- Can work with receiving, stock entries, and pick lists.
- Currently has read access to products and warehouses, but does not create product/location master data.

### Business Owner

- Login: `see BUSINESS_OWNER_USER in .env`
- Password: `see BUSINESS_OWNER_PASSWORD in .env`
- Purpose: owner-level testing and system setup.
- Can create/edit warehouses, products, item groups, UOMs, users, roles, and stock documents.
- Starts in the warehouse interface but has broad system permissions.

### Client Portal User

- Login: `alpha.client@example.test`
- Password: `see CLIENT_PORTAL_PASSWORD in .env`
- Purpose: client-side Receiving Notice testing.
- Linked customer: `Demo Client Alpha`.
- Uses the client portal, not ERPNext Desk.

## What Is Ready To Test

## Recommended Demo Walkthrough

Use this sequence for the first customer review.

1. Log in as the Client Portal User and create a new Receiving Notice for `Demo Client Alpha`.
2. Open Inventory in the portal and confirm only Alpha stock is visible.
3. Open Shipment Requests in the portal and create a simple outbound request.
4. Open Discrepancy Instructions in the portal and submit an instruction for `ASN-ALPHA-001`.
5. Log in as the Warehouse Operator and open `3PL Warehouse`.
6. Open `ASN-ALPHA-001`, confirm expected vs received quantities and the quantity discrepancy.
7. Open `BOX-ALPHA-001`, confirm it is linked to the notice and temporary receiving location.
8. Log in as the Business Owner and confirm products and warehouse locations can be created or edited.

This walkthrough covers the current MVP boundary: client portal input, customer data isolation, receiving notice review, discrepancy tracking, container/box visibility, and owner-level administration.

The deploy validator now checks these same boundaries automatically: internal warehouse logins, business-owner master-data pages, client portal routes, demo records, and Alpha-vs-Beta data isolation.

## Pre-Client Golden Path Validation

Before giving the instance to a customer for testing, run:

```bash
./scripts/validate_mvp_e2e.sh
```

This server-side validation creates temporary MVP test data, runs the core flow, and removes the temporary records afterward.

Covered flow:

1. Client creates a product card.
2. Product card synchronizes into ERPNext `Item`.
3. Client creates a structured Receiving Notice.
4. Warehouse receives goods into `Temporary Receiving - 3`.
5. Receiving Notice is compared and marked received.
6. Warehouse creates/uses a container box.
7. Container is put away into storage.
8. Warehouse runs a no-difference stocktake.
9. Client creates a Shipment Request.
10. System creates a Pick List and allocates stock.
11. Warehouse confirms picking.
12. Warehouse packs the shipment.
13. Warehouse ships the shipment.
14. Client visibility for own product and shipped request is verified.

Expected result:

- Command ends with `MVP E2E validation passed`.
- No temporary `MVP-E2E-*` records remain after cleanup.
- Existing demo data remains available for manual customer review.

### Client Portal

Open `https://erpnext.77.237.244.169.sslip.io/client/receiving-notice`.

Test:

- Log in as `alpha.client@example.test`.
- Create a Receiving Notice for `Demo Client Alpha`.
- Add expected products and quantities in the `Expected Products` table.
- Try to use another customer only as a negative test.

Expected result:

- Client can create Receiving Notices through the portal.
- Client user is a `Website User`, not a Desk/System user.
- User permission restricts the client to `Demo Client Alpha`.
- Client must not see or create records for `Demo Client Beta`.

Additional client portal routes:

- Inventory: `https://erpnext.77.237.244.169.sslip.io/client/inventory`
- Shipment Requests: `https://erpnext.77.237.244.169.sslip.io/client/shipment-request`
- Shipment Tracking: `https://erpnext.77.237.244.169.sslip.io/client/shipment-tracking`
- Discrepancies: `https://erpnext.77.237.244.169.sslip.io/client/discrepancies`
- Discrepancy Instructions: `https://erpnext.77.237.244.169.sslip.io/client/discrepancy-instruction`

Expected result:

- Client can view customer-restricted inventory snapshots.
- Client can create shipment requests.
- Client can track shipment request status.
- Client can review receiving discrepancies.
- Client can send instructions for receiving discrepancies.

### Warehouse Landing

After login, the user should land in `3PL Warehouse`.

Expected result:

- No setup wizard.
- No `Page not found`.
- No `Not permitted`.
- Warehouse menu opens.

### Product And Warehouse Master Data

Use the Business Owner account.

Test:

- Open `Item`.
- Create or edit a test product.
- Open `Warehouse`.
- Create or edit a test storage location.

Expected result:

- Owner can create and edit products and warehouses.

### Receiving Notice

Open `Inbound Shipment Notice`.

Test:

- View existing demo notice `ASN-ALPHA-001`.
- Confirm expected products have `Client SKU` values.
- Confirm the notice has one demo discrepancy for `SKU-ALPHA-002`.
- Create a new receiving notice with expected products and quantities.

Expected result:

- Notice can be created and saved.
- It can reference a client and expected items.
- Discrepancies can be stored on the receiving notice.

### Containers / Boxes

Open `Three PL Container` / `Containers`.

Test:

- Open demo container `BOX-ALPHA-001`.
- Confirm it belongs to `Demo Client Alpha`.
- Confirm it is linked to `ASN-ALPHA-001`.
- Confirm it is currently in `Temporary Receiving - 3`.
- Confirm it contains `SKU-ALPHA-001` and `SKU-ALPHA-002`.

Expected result:

- A cardboard box can be tracked as a separate warehouse container.
- Products inside the box are visible before final putaway.
- The box can stay in receiving, move to storage, then be used during picking/packing later.

### Client Data Isolation

Use the Client Portal User.

Test:

- Confirm portal inventory contains Alpha products such as `SKU-ALPHA-001`.
- Confirm Beta data such as `SKU-BETA-001` / `Demo Client Beta` is not available to the client.
- Confirm Beta receiving notice `ASN-BETA-001` is not available to the Alpha client.
- Try creating a Receiving Notice or Shipment Request for another customer only as a negative test.

Expected result:

- The client can work only with their own customer account.
- Cross-customer create/read operations are blocked by server-side permissions.

### Receiving And Stock Entry

Open `Stock Entry`.

Test:

- Create a Material Receipt into `Temporary Receiving - 3`.
- Use demo client, receiving notice, scanned location, and container fields where available.
- Compare received quantity against the receiving notice.

Expected result:

- Goods can be received into temporary receiving.
- Stock is not placed directly into final storage.
- The container/box reference can be recorded on the stock entry.

Scanner alternative:

- Open `https://erpnext.77.237.244.169.sslip.io/warehouse/receiving`.
- Scan or enter ASN, container, expected item, quantity, and receiving location.
- Submit the receipt.

Expected scanner result:

- A submitted inbound receipt Stock Entry is created.
- The container contents are updated.
- The Receiving Notice received and variance quantities are updated.
- Movement history shows movement type `Received`.

### Putaway

Open the scanner-first page:

`/warehouse/putaway`

Test:

- Scan or enter a container that is ready for putaway.
- Scan or enter a storage location such as `Aisle A - 3` or `Aisle B - 3`.
- Apply putaway.

Expected result:

- The container moves from receiving/verification into storage.
- The container status becomes `Stored`.
- Movement history shows movement type `Putaway`.

The standard ERPNext Stock Entry putaway flow is still available for full stock-ledger transfers.

### Warehouse Corrections

Open the scanner-first page:

`/warehouse/correction`

Test:

- Scan or enter a container.
- Scan or enter an item.
- Enter the actual quantity found in the box.
- Select correction type and condition.
- Apply correction.

Expected result:

- A `Three PL Warehouse Correction` record is created.
- Container contents are updated to the actual quantity.
- Damaged, quality, or hold corrections move the container into verification.
- Movement history shows movement type `Adjusted`.

Current boundary:

- Clear quantity deltas create `3PL Quantity Gain` or `3PL Quantity Loss` Stock Entries.
- If ERPNext cannot post the Stock Entry automatically, the correction is marked `Needs Review` for manager review.

### Stocktake

Open the scanner-first page:

`/warehouse/stocktake`

Test:

- Scan or enter a container.
- Scan or enter an item.
- Enter the counted quantity found in the box.
- Select condition.
- Apply stocktake.

Expected result:

- A `Three PL Stocktake` record is created.
- If counted quantity equals system quantity and condition is `OK`, status is `No Difference`.
- If there is a difference, a linked `Three PL Warehouse Correction` is created.
- Container contents are updated to the counted quantity.
- Movement history shows movement type `Adjusted` for count deltas.

### Picking

Open `Pick List`.

Test:

- Open the Pick List generated from `SHIP-ALPHA-001`, or create a manual pick list using available demo stock.

Expected result:

- Picking workflow opens and references stock locations and containers.

### Repack / Box Consolidation

Open the scanner-first page:

`/warehouse/repack`

Test:

- Scan one or more source containers.
- Enter a new target container code.
- Enter a storage location such as `Aisle A - 3`.
- Apply repack.

Expected result:

- Source containers become `Replaced`.
- Source containers reference the new target container.
- Target container is created or updated as `Stored`.
- Target contents equal the sum of source container contents.
- Movement history shows movement type `Repacked`.

## Current Scope Limits

- Client portal MVP is implemented for creating Receiving Notices.
- Client inventory visibility is implemented as an MVP snapshot.
- Shipment requests are implemented as portal MVP records.
- Client shipment tracking is implemented as a portal MVP page.
- Client discrepancy review is implemented as a portal MVP page.
- Structured shipment requests are converted to draft Pick Lists as an MVP.
- Outbound status updates after packing/dispatch are implemented as MVP through submitted packing/shipping Stock Entries.
- Box/container handling exists as a first ERPNext custom DocType model. Scanner-first pages exist for receiving, container moves, putaway, warehouse corrections, stocktake, full-container repack, partial split, picking confirmation, and outbound fulfillment; grouped stocktake sessions and richer multi-item split guidance still need polish.
- Real email delivery is not configured.
- A placeholder outgoing email account exists only to prevent ERPNext forms from failing when an outgoing account is required.

## Product Ownership Direction

Current test assumption:

- Each product belongs to one client.
- Product codes are unique between clients.

Recommended architecture:

- Store `client` and `client_sku` as separate product fields.
- Use a generated visible code such as `CLIENTABBR-SKU` for readability.
- Do not rely only on a text prefix as the long-term ownership model.
- Treat `Owner Client + Client SKU` as the business identity of a product.

This keeps the current setup simple while leaving room for multiple clients to store the same SKU later.
