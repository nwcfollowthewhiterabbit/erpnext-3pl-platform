# Client Test Guide

Use this guide for the current ERPNext 3PL test instance.

## URL

`https://erpnext.77.237.244.169.sslip.io`

## Test Accounts

### Warehouse Operator

- Login: `warehouse.demo@example.test`
- Password: `WarehouseDemo2026!`
- Purpose: receiving, stock entries, pick lists, basic warehouse operations.
- Not intended for system setup or master-data administration.

### Warehouse Manager

- Login: `warehouse.manager@example.test`
- Password: `WarehouseManager2026!`
- Purpose: warehouse operations with manager-level stock rights.
- Can work with receiving, stock entries, and pick lists.
- Currently has read access to products and warehouses, but does not create product/location master data.

### Business Owner

- Login: `rupusm@gmail.com`
- Password: `6elz4oeiuUGAHSGRccwngNmb`
- Purpose: owner-level testing and system setup.
- Can create/edit warehouses, products, item groups, UOMs, users, roles, and stock documents.
- Starts in the warehouse interface but has broad system permissions.

## What Is Ready To Test

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
- Create a new receiving notice with expected products and quantities.

Expected result:

- Notice can be created and saved.
- It can reference a client and expected items.

### Receiving And Stock Entry

Open `Stock Entry`.

Test:

- Create a Material Receipt into `Temporary Receiving - 3`.
- Use demo client/item fields where available.
- Compare received quantity against the receiving notice manually.

Expected result:

- Goods can be received into temporary receiving.
- Stock is not placed directly into final storage.

### Putaway

Open `Stock Entry`.

Test:

- Create a Material Transfer from `Temporary Receiving - 3` to a storage location such as `Aisle A - 3`.

Expected result:

- Stock can move from receiving into storage.

### Picking

Open `Pick List`.

Test:

- Create a pick list using available demo stock.

Expected result:

- Picking workflow opens and can reference stock locations.

## Current Scope Limits

- Client portal is not implemented yet.
- Clients cannot yet log in and create receiving notices themselves.
- Client inventory visibility is not implemented yet.
- Shipment requests and outbound client portal flow are not implemented yet.
- Box/container handling is still an open design question.
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

This keeps the current setup simple while leaving room for multiple clients to store the same SKU later.
