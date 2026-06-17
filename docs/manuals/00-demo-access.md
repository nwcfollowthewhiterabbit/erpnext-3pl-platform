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

## Client Desk User

- Login: `alpha.client@example.test`
- Password: `see CLIENT_DESK_PASSWORD in .env`
- Intended use: client-side MVP testing for `Demo Client Alpha`.
- Desk URL: `https://erpnext.77.237.244.169.sslip.io/desk/3pl-client`
- This is a restricted ERPNext Desk user. The user starts in the `3PL Client` Workspace and is limited by role, module profile, User Permission, and server-side customer guards.
- Client work uses the restricted ERPNext Desk workspace for MVP1.

## Starting Point

For warehouse/admin users, after login go to:

- `Stock`
- `Inbound Shipment Notice`
- `Stock Entry`
- `Pick List`
- `Warehouse`
- `Item`

For client testing, log in and open the `3PL Client` Workspace:

- `desk/3pl-client`
- Receiving Notices
- Products
- Inventory reports
- Shipment Requests
- Discrepancies / client instructions
