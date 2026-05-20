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

## Picking and Shipping

1. Create a Pick List.
2. Pick products from locations according to the Pick List.
3. Pack and ship products.

## Desired Improvements

- When moving products between locations, or during put-away/picking, scan both the location and the product.
- Track which client the products came from. Stock Entry does not include this by default, so this needs a custom field or a custom workflow extension.

