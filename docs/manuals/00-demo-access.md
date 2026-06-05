# Demo Access

## URL

`https://erpnext.77.237.244.169.sslip.io`

## Administrator

- Login: `Administrator`
- Password: stored in the server `.env` as `ADMIN_PASSWORD`

## Warehouse Demo User

- Login: `warehouse.demo@example.test`
- Password: `see WAREHOUSE_OPERATOR_PASSWORD in .env`
- Intended use: operator-level Stock workflow testing.

## Warehouse Manager User

- Login: `warehouse.manager@example.test`
- Password: `see WAREHOUSE_MANAGER_PASSWORD in .env`
- Intended use: manager-level Stock workflow testing.

## Business Owner User

- Login: `see BUSINESS_OWNER_USER in .env`
- Password: `see BUSINESS_OWNER_PASSWORD in .env`
- Intended use: owner-level access. Starts on the warehouse management landing page and receives all standard system roles, including `System Manager`, `Stock Manager`, and `Item Manager`.

## Client Portal User

- Login: `alpha.client@example.test`
- Password: `see CLIENT_PORTAL_PASSWORD in .env`
- Intended use: client-side portal testing for `Demo Client Alpha`.
- Portal URL: `https://erpnext.77.237.244.169.sslip.io/client/receiving-notice`
- This is a `Website User`, not an ERPNext Desk user.

## Starting Point

For warehouse/admin users, after login go to:

- `Stock`
- `Inbound Shipment Notice`
- `Stock Entry`
- `Pick List`
- `Warehouse`
- `Item`

For client portal testing, open:

- `client/receiving-notice`
- `client/inventory`
- `client/shipment-request`
- `client/discrepancy-instruction`
