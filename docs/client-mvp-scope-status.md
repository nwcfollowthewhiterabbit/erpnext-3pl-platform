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
| Receiving products | 80% | Implemented as MVP. Client can create Receiving Notice; warehouse can receive into temporary area; expected vs actual quantities are synced; discrepancies are stored. Remaining work is more polished confirmation/status actions. |
| Location movement | 75% | Implemented through container/HU moves and movement history. Good enough for MVP testing. Remaining work is stronger operational validation and real warehouse location naming import. |
| Sending orders | 70% | Implemented as MVP. Client can create Shipment Request; system creates Pick Lists; warehouse can confirm picking and outbound packing/shipping. Remaining work is labels, carrier/tracking integrations, and more polished shipment status UX. |
| Warehouse corrections | 75% | Implemented as MVP. Corrections can adjust container contents, record movement history, and post clear quantity deltas to ERPNext Stock Entry. Ambiguous cases go to Needs Review. Remaining work is richer approval workflow. |
| Inventory / stocktake | 70% | Implemented as MVP. Stocktake records counted vs system quantity and links deltas to corrections. Remaining work is grouped stocktake sessions for larger counts. |
| Product balance on selected day | 70% | Implemented through daily inventory balance snapshots and `3PL Inventory Balance By Date`. Limitation: history starts from the day snapshots are generated, not before. |
| Warehouse operation turnover | 75% | Implemented through container movement history and `3PL Warehouse Operation Turnover`. Remaining work is report filtering/presentation polish for client-facing usage. |

Overall MVP readiness for the client's described scope: approximately 75-80%.

## What Is Ready For Customer Testing

### Roles

Ready:

- Client portal user.
- Warehouse operator.
- Warehouse manager.
- Business owner / admin-like user.

Test expectation:

- Client works in the portal and does not need ERPNext Desk.
- Warehouse roles work in the warehouse workspace and warehouse operation pages.
- Business owner can administer the system and access warehouse flows.

### Receiving Products

Ready:

- Client Receiving Notice portal flow.
- Inbound Shipment Notice data model.
- Temporary receiving area.
- Warehouse receiving operation.
- Expected vs actual received quantity comparison.
- Discrepancy rows for missing, unexpected, damaged, and quality issue cases.
- Client instructions for discrepancies as separate portal records.

Not fully polished yet:

- Final workflow buttons such as "confirm receiving", "notify client", "client approved discrepancy", and similar status transitions.
- Rich discrepancy detail page for the client.

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

- Client Shipment Request portal flow.
- Structured shipment request item rows.
- Draft Pick List creation from client request.
- Picking confirmation.
- Packing and shipping operation pages.
- Shipment/container status updates from outbound stock entries.

Not fully polished yet:

- Carrier labels.
- Tracking numbers and courier integrations.
- More customer-friendly shipment tracking screen.

### Warehouse Corrections

Ready:

- Quantity correction.
- Unexpected product correction.
- Damaged product / quality issue correction.
- Hold-for-review path.
- Clear quantity deltas create ERPNext Stock Entries where the ledger allows it.
- Manager review queue for corrections that cannot be posted automatically.

Not fully polished yet:

- Approval workflow with named approver, comments, timestamps, and final decision.
- More guided UI for ambiguous correction cases.

### Inventory / Stocktake

Ready:

- Stocktake by container/location/SKU.
- Counted quantity vs system quantity.
- Linked correction if there is a delta.
- Stocktake report.

Not fully polished yet:

- Grouped stocktake sessions.
- Larger count workflow with many lines, assignments, and review states.

### Reports

Ready:

- `3PL Client Inventory`.
- `3PL Client Inventory Summary`.
- `3PL Inventory Balance By Date`.
- `3PL Warehouse Operation Turnover`.
- Supporting reports for receiving, discrepancies, containers, moves, repacks, corrections, stocktakes, and shipment requests.

Not fully polished yet:

- Client-facing presentation and filters can be improved after the customer confirms exact columns and period logic.
- Historical balance report cannot reconstruct dates before snapshot capture existed.

## Current Main Gaps For This MVP

These are the remaining gaps specifically for the client's described MVP:

1. Polish receiving confirmation statuses and discrepancy decision workflow.
2. Import or create the real warehouse location hierarchy after naming convention is agreed.
3. Add stronger guards around location/container moves.
4. Polish outbound shipment status screen for the client.
5. Add grouped stocktake sessions.
6. Add richer correction approval workflow for Needs Review cases.
7. Improve client-facing report filters and presentation.

## Recommended Next Local Task

Finish the "customer-testable MVP" layer:

1. Add a simple MVP dashboard / guide page for the client and warehouse manager with links only to the flows in this document.
2. Polish status transitions for Receiving Notice and Shipment Request.
3. Add grouped stocktake sessions.
4. Add correction approval actions for Needs Review.
5. Add customer-friendly filters to the two required reports.

