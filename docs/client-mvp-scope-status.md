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

## Scope Guardrails

This file is the source of truth for the customer-requested MVP1 scope.

MVP1 manual testing should not include `Three PL Client Product Import` / bulk product import. Product import exists only as a post-MVP1 roadmap/admin capability and must stay outside the client MVP1 workspace.

Client product maintenance for MVP1 means:

- create/edit products through `Three PL Client Product`;
- synchronize product cards to ERPNext `Item`;
- optionally use Product Export for review/reporting.

Bulk Product Import is not part of MVP1 acceptance.

## Added Beyond The Customer's Minimal MVP1

These features are available or partially available for testing, but they go beyond the customer's original minimal request:

| Feature | MVP1 relation | Status |
| --- | --- | --- |
| Receiving Scan | Convenience layer over warehouse receiving. MVP1 can also be tested through standard `Stock Entry`. | Available for testing. |
| Receiving Review | Convenience review screen for inbound notices. | Available for testing. |
| Container / Handling Unit model | More detailed than the customer's original request, but now used as the warehouse operating model. | Available for testing. |
| Container scanner pages | Convenience pages for moves, putaway, correction, stocktake, picking, and outbound fulfillment. | Available for testing. |
| Container Repack / split / consolidation | Not required by MVP1, but useful when whole-container allocation needs a matching box. | Available for testing as extended warehouse functionality. |
| Correction Review | Review queue beyond simple correction entry. | Available for testing. |
| Stocktake Session | Grouping layer beyond simple stocktake. | Available for testing. |
| Picking Confirmation | Dedicated picking confirmation screen beyond basic shipment request flow. | Available for testing. |
| Outbound Fulfillment | Dedicated packing/shipping screen beyond basic dispatch records. | Available for testing. |
| Client Product Catalog | More structured than manually maintaining ERPNext Items directly. | Available for testing. |
| Product Export | Not explicitly requested, but useful for client product review. | Available for testing. |
| Product Import / bulk import | Not part of MVP1. | Roadmap/post-MVP1 only. Do not include in MVP1 manual testing. |
| Shipment Tracking | Convenience client view beyond basic shipment request status. | Available for testing. |
| Discrepancy Instructions | Structured client response to receiving discrepancies. | Available for testing. |
| Extended container/movement reports | More detailed than the two requested reports. | Available for testing where visible. |

## Readiness Summary

| Area | MVP readiness | Current status |
| --- | ---: | --- |
| User roles | 90% | Implemented and tested for client, warehouse operator, warehouse manager, and business owner. Remaining work is role polish after customer feedback. |
| Receiving products | 90% | Implemented as MVP. Client creates Receiving Notices from the restricted ERPNext Desk `3PL Client` Workspace; warehouse can receive into temporary area; expected vs actual quantities are synced; discrepancies are stored. Warehouse review actions now exist for confirming received, waiting for client, and closing active notices. |
| Location movement | 75% | Implemented through container/HU moves and movement history. Good enough for MVP testing. Remaining work is stronger operational validation and real warehouse location naming import. |
| Sending orders | 80% | Implemented as MVP with whole-container allocation. Client creates Shipment Requests from the restricted ERPNext Desk `3PL Client` Workspace; system creates Pick Lists when requested quantities match complete available containers; warehouse can confirm picking and outbound packing/shipping. Partial picks require split/repack into a new target container before allocation; the original shelf box keeps its container number and remaining quantity. Warehouse review actions now exist for accept, close, and cancel. Remaining work is labels, carrier/tracking integrations, outbound courier parcel handling, and richer quantity-level reservation. |
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
- Outbound courier parcel / tracking label flow. If the courier tracking number is only a reference, keep it on the shipment. If the warehouse physically creates a parcel per order, model it as a short-lived outbound Handling Unit. Use scan-first input for readable labels and manual entry fallback for non-standard labels.
- Quantity-level reservation inside one mixed or oversized container. For MVP, split/repack the picked quantity into a new target container first, keep the original shelf box number unchanged, and then allocate the matching target container.

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
2. Add stronger guards around location/container moves.
3. Add carrier labels / tracking integrations if required.
4. Add richer count assignments/review states for large stocktakes.
5. Add multi-step correction approval if the client wants more than manager decision metadata.
6. Improve client-facing report filters and presentation.

## Recommended Next Local Task

Finish the "customer-testable MVP" layer:

1. Agree warehouse location naming convention with the client and import the real location hierarchy.
2. Add customer-friendly filters to the two required reports if the current Desk reports are not enough.
3. Add carrier labels / tracking integrations if required.
4. Add outbound courier parcel / tracking label flow if the physical warehouse process requires one parcel per order.
5. Add richer count assignments/review states for large stocktakes.
