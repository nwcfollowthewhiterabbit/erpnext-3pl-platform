# Client MVP Scope Status

This document tracks only the MVP scope explicitly described by the client.
It does not replace the full roadmap; it is the focused local task for the first customer-testable version.

## Scope From Client

The client asked for:

1. User roles.
2. Receiving products: client enters a notice, warehouse receives, compares, and confirms.
3. Moving products between warehouse locations.
4. Sending orders: client enters an order, warehouse picks, prepares, and dispatches.
5. Warehouse corrections: wrong quantity in a box, damaged/mismatched goods, or similar corrections.
6. Inventory / stocktake.
7. Reports:
   - product balance on a selected day for the client;
   - warehouse operation turnover for a selected period for client and warehouse users.

## Readiness Summary

| Area | MVP readiness | Current status |
| --- | ---: | --- |
| User roles | 90% | Implemented and tested for client, warehouse operator, warehouse manager, and business owner. Remaining work is role polish after customer feedback. |
| Receiving products | 90% | Implemented as MVP. Client creates Receiving Notices from the restricted ERPNext Desk `3PL Client` Workspace; warehouse can receive into temporary area; expected vs actual quantities are synced; discrepancies are stored. Warehouse review actions now exist for confirming received, waiting for client, and closing active notices. |
| Location movement | 75% | Implemented through container/HU moves and movement history. Good enough for MVP testing. Remaining work is stronger operational validation and real warehouse location naming import. |
| Sending orders | 80% | Implemented as MVP with whole-container allocation. Client creates Shipment Requests from the restricted ERPNext Desk `3PL Client` Workspace; system creates Pick Lists when requested quantities match complete available containers; warehouse can confirm picking and outbound packing/shipping. Partial picks require split/repack before allocation. Warehouse review actions now exist for accept, close, and cancel. Remaining work is labels, carrier/tracking integrations, and richer quantity-level reservation. |
| Warehouse corrections | 85% | Implemented as MVP. Corrections can adjust container contents, record movement history, and post clear quantity deltas to ERPNext Stock Entry. Ambiguous cases go to Needs Review with manager review actions and review metadata. |
| Inventory / stocktake | 85% | Implemented as MVP. Stocktake records counted vs system quantity, links deltas to corrections, and now supports grouped stocktake sessions. Remaining work is richer assignment/review UX for large physical counts. |
| Product balance on selected day | 70% | Implemented through daily inventory balance snapshots and `3PL Inventory Balance By Date`. Limitation: history starts from the day snapshots are generated, not before. |
| Warehouse operation turnover | 75% | Implemented through container movement history and `3PL Warehouse Operation Turnover`. Remaining work is report filtering/presentation polish for client-facing usage. |

Overall MVP readiness for the client's described scope: approximately 87-90%.

## What Is Ready For Customer Testing

### Roles

Ready:

- Client Desk user with restricted `3PL Client` Workspace.
- Warehouse operator.
- Warehouse manager.
- Business owner / admin-like user.

Test expectation:

- Client works in ERPNext Desk, but only through the restricted `3PL Client` Workspace and customer-scoped permissions.
- Warehouse roles work in the warehouse workspace and warehouse operation pages.
- Business owner can administer the system and access warehouse flows.

### Receiving Products

Ready:

- Client Receiving Notice Desk flow.
- Inbound Shipment Notice data model.
- Temporary receiving area.
- Warehouse receiving operation.
- Expected vs actual received quantity comparison.
- Discrepancy rows for missing, unexpected, damaged, and quality issue cases.
- Client instructions for discrepancies as separate customer-scoped records.
- Warehouse review page at `/warehouse/receiving-review` for confirming received notices, marking notices as waiting for client, and closing notices.
- Client sees relevant discrepancy/instruction documents and reports through the `3PL Client` Workspace.

Not fully polished yet:

- More formal approval history for client discrepancy decisions.

### Moving Products Between Locations

Ready:

- Warehouse locations use ERPNext `Warehouse` hierarchy.
- Boxes / cartons / HUs are modeled as `Three PL Container`, not as warehouse locations.
- Container movement between locations is recorded.
- Movement history is available.
- Putaway from receiving to storage location is available.

Not fully polished yet:

- Real warehouse location tree still needs customer naming convention.
- Extra guards for impossible moves, closed containers, and replaced containers.

### Sending Orders

Ready:

- Client Shipment Request Desk flow.
- Structured shipment request item rows.
- Draft Pick List creation from client request when available containers exactly cover the requested quantities.
- Picking confirmation at container level.
- Packing and shipping operation pages.
- Shipment/container status updates from outbound stock entries.
- Warehouse review page at `/warehouse/shipment-review` for accepting, closing, or cancelling active shipment requests.
- Client sees Shipment Request status through the `3PL Client` Workspace and client reports.

Not fully polished yet:

- Carrier labels.
- Tracking numbers and courier integrations.
- Quantity-level reservation inside one mixed or oversized container. For MVP, split/repack first and then allocate the matching container.

### Warehouse Corrections

Ready:

- Quantity correction.
- Unexpected product correction.
- Damaged product / quality issue correction.
- Hold-for-review path.
- Clear quantity deltas create ERPNext Stock Entries where the ledger allows it.
- Manager review queue for corrections that cannot be posted automatically.
- Manager review metadata: decision, reviewer, reviewed timestamp, and review notes.

Not fully polished yet:

- More guided UI for ambiguous correction cases.
- Multi-step approval workflow if the client wants more than one reviewer.

### Inventory / Stocktake

Ready:

- Stocktake by container/location/SKU.
- Grouped stocktake sessions.
- Counted quantity vs system quantity.
- Linked correction if there is a delta.
- Stocktake report.
- Stocktake session report.

Not fully polished yet:

- Larger count workflow with many lines, assignments, and review states.

### Reports

Ready:

- `3PL Client Inventory`.
- `3PL Client Inventory Summary`.
- `3PL Inventory Balance By Date`.
- `3PL Warehouse Operation Turnover`.
- Supporting reports for receiving, discrepancies, containers, moves, repacks, corrections, stocktakes, and shipment requests.

Not fully polished yet:

- Client-facing Desk report filters/presentation can be improved after the customer confirms exact columns and period logic.
- Historical balance report cannot reconstruct dates before snapshot capture existed.

## Current Main Gaps For This MVP

These are the remaining gaps specifically for the client's described MVP:

1. Import or create the real warehouse location hierarchy after naming convention is agreed.
3. Add stronger guards around location/container moves.
4. Add carrier labels / tracking integrations if required.
5. Add richer count assignments/review states for large stocktakes.
6. Add multi-step correction approval if the client wants more than manager decision metadata.
7. Improve client-facing report filters and presentation.

## Recommended Next Local Task

Finish the "customer-testable MVP" layer:

1. Agree warehouse location naming convention with the client and import the real location hierarchy.
2. Add customer-friendly filters to the two required reports if the current Desk reports are not enough.
3. Add carrier labels / tracking integrations if required.
4. Add richer count assignments/review states for large stocktakes.
