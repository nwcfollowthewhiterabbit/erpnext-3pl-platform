# Client Requirements

## Scope

- Start with ERPNext only, without integrations with external systems.
- Use ERPNext exclusively for warehouse management.
- Disable or hide modules that are not needed for the initial workflow, including Accounting, Buying, Selling, and similar business areas.
- Keep Stock/Warehouse functionality and only the dependencies needed for ERPNext to work correctly.

## Receiving Products

1. Receive a shipment notification from the client.
2. Receive products into a temporary warehouse for comparison using Stock Entry.
3. Compare the notification against the actual received products.
4. Put products away into warehouse locations.

## Minimum Working Flows Confirmed By Client

The client confirmed that the first useful version should focus on these flows:

1. User roles.
2. Receiving products: client enters the notice, warehouse receives, compares, and confirms.
3. Moving products by warehouse locations.
4. Sending orders: client enters an order, warehouse picks, prepares, and dispatches.
5. Warehouse corrections: wrong quantity in a box, damaged/mismatched goods, or similar operational corrections.
6. Inventory / stocktake.

Initial reporting scope:

1. Client product balance on a selected date.
2. Warehouse operation turnover for a selected period, visible for both client and warehouse users.

## Stage MVP2 Requirement: Product Card Management

The next-stage client requirement is product master data ownership. The base portal flow is now implemented; Excel import/export remains pending.

1. The client creates new product cards through the client portal.
2. The client updates existing product cards through the client portal.
3. Each product card can have a photo.
4. The client deactivates products instead of deleting master records.
5. Product changes are logged.
6. Product data should later be exported and imported through an Excel table.

Expected direction:

- Keep ERPNext `Item` as the base product record.
- Treat `Owner Client + Client SKU` as the product business identity.
- Expose product maintenance through the client portal, not through unrestricted Desk access.
- Validate that clients can only manage their own products.

## Picking and Shipping

1. Create a Pick List.
2. Pick products from locations according to the Pick List.
3. Pack and ship products.

## Desired Improvements

- When moving products between locations, or during put-away/picking, scan both the location and the product.
- Track which client the products came from. Stock Entry does not include this by default, so this needs a custom field or a custom workflow extension.
- Keep warehouse location renaming as an administrative/setup operation, not a normal warehouse manager action.
