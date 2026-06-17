# Live Flow Reliability Backlog

This document records implementation work found during the MVP flow audit.

The common issue is that some flows are correct when the maintenance processor is run, but the user-facing UI result is not always created immediately after the user action. For the MVP, normal client and warehouse actions must update the next operational document without requiring a manual sync command.

## Reliability Rule

- Primary MVP flows must update their derived records immediately after the relevant user action.
- Batch processors should remain as recovery and maintenance tools.
- Tests must distinguish processor behavior from live UI behavior.
- A flow should not be marked ready for client testing if the expected result appears only after a manual processor call.

## Already Stabilized

These gaps are stabilized in the current MVP configuration:

- Client Product save creates or updates the linked ERPNext Item immediately.
- Receiving Notice save recalculates expected-vs-received discrepancies immediately.
- Discrepancy Instruction save updates the linked Receiving Notice client-instruction status immediately.
- Container save updates the client-facing Inventory Snapshot immediately, including putaway status/location changes.
- Structured client Receiving Notice save expands product-picker rows into child item rows immediately.
- Shipment Request save creates or updates the warehouse Pick List and marks allocated containers immediately.
- Product saves synchronize ERPNext Items immediately. CSV Product Import is retained as a post-MVP1/admin capability, not as a required MVP1 client flow.
- Stock Entry submit immediately syncs inbound receipt, packing, and shipping results.
- Pick List save immediately syncs fully picked container rows.

## Work To Execute

| ID | Flow | Current Gap | Expected Behavior | Implementation Direction | Required Tests | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| LFR-01 | Client Shipment Request to Pick List | Fixed. Processor remains as recovery. | After client submits a shipment request, warehouse users immediately see the Pick List and allocated containers. | Server Script: `3PL Shipment Request Immediate Pick List Sync`. | Live validation asserts Pick List exists and request/container statuses update without calling the processor. | Done |
| LFR-02 | Product Cards to Items | Fixed for direct product cards. Import remains post-MVP1/admin capability. | After client saves a product card, the linked ERPNext Item is created/updated immediately. | Product saves trigger `3PL Client Product Immediate Sync`. | Live validation asserts product card sync and linked Item without requiring Product Import. | Done |
| LFR-03 | Standard Stock Entry Submit | Fixed. Processor remains as recovery. | Submitting an inbound receipt or outbound packing/shipping Stock Entry immediately updates the linked Receiving Notice, Shipment Request, containers, movements, and inventory snapshots. | Server Script: `3PL Stock Entry Immediate Flow Sync`. | Live validation submits Stock Entries and asserts linked documents update without manual processor calls. | Done |
| LFR-04 | Standard Pick List Picked Qty | Fixed. Processor remains as recovery. | When a warehouse user confirms picked quantities in Pick List, linked containers update immediately. | Server Script: `3PL Pick List Immediate Picked Sync`. | Live validation updates picked qty and asserts container status/movement without manual processor calls. | Done |
| LFR-05 | Test Suite Design | Improved for MVP live flows. | Live-flow tests prove immediate UI/server behavior; processors remain tested through deployment/recovery paths. | Deployment, client Desk, and warehouse operation packs now include immediate-behavior checks. | `erpnext_3pl.validation.site`, `erpnext_3pl.validation.warehouse_ops`, and targeted Desk-native validation. | Done |
| LFR-06 | Documentation Boundaries | Updated. | Docs distinguish immediate behavior and recovery processors. | Keep this file and process docs aligned after future flow changes. | Documentation review against implemented behavior. | Done |

## Notes For Implementation

- Do not remove existing processors. They are useful for deployment, repair, and periodic reconciliation.
- Prefer small server scripts/hooks that call the existing processor functions for one document where possible.
- Avoid duplicating business logic between hooks, portal pages, and batch processors.
- After each item is implemented, run both automated validation and a browser/manual flow check with the relevant role.
- Product Import remains covered by the processor path for post-MVP1/admin use.
