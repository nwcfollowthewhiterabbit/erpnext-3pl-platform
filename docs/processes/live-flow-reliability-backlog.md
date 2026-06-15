# Live Flow Reliability Backlog

This document records implementation work found during the MVP flow audit.

The common issue is that some flows are correct when the maintenance processor is run, but the user-facing UI result is not always created immediately after the user action. For the MVP, normal client and warehouse actions must update the next operational document without requiring a manual sync command.

## Reliability Rule

- Primary MVP flows must update their derived records immediately after the relevant user action.
- Batch processors should remain as recovery and maintenance tools.
- Tests must distinguish processor behavior from live UI behavior.
- A flow should not be marked ready for client testing if the expected result appears only after a manual processor call.

## Already Stabilized

These gaps were fixed before this backlog was written:

- Client Product save creates or updates the linked ERPNext Item immediately.
- Receiving Notice save recalculates expected-vs-received discrepancies immediately.
- Discrepancy Instruction save updates the linked Receiving Notice client-instruction status immediately.
- Container save updates the client-facing Inventory Snapshot immediately, including putaway status/location changes.

## Work To Execute

| ID | Flow | Current Gap | Expected Behavior | Implementation Direction | Required Tests | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| LFR-01 | Client Shipment Request to Pick List | `Three PL Shipment Request` is converted to ERPNext Pick List by `scripts/sync_shipment_requests.py`. | After client submits a shipment request, warehouse users immediately see the Pick List and allocated containers. | Add save/submit automation for shipment requests. Keep the processor as recovery. | Portal creates shipment request; test asserts Pick List exists and request/container statuses are updated without calling the processor. | High |
| LFR-02 | Product Import to Products/Items | Product imports can remain `Pending` until `scripts/sync_client_products.py` processes them. | After client uploads/imports a file, products are created/updated and import status changes to `Applied` or `Failed` immediately. | Add save/submit automation for `Three PL Client Product Import`. Keep the processor as recovery. | Portal imports CSV/XLSX; test asserts import status, client product, and linked Item without calling the processor. | High |
| LFR-03 | Standard Stock Entry Submit | Desk-created Stock Entries can require receiving/outbound processors to update linked 3PL documents. | Submitting an inbound receipt or outbound packing/shipping Stock Entry immediately updates the linked Receiving Notice, Shipment Request, containers, movements, and inventory snapshots. | Add Stock Entry submit hook/server script for inbound receipt, packing, and shipping flows. | Desk-like Stock Entry submit tests for inbound and outbound flows without manual processor calls. | High |
| LFR-04 | Standard Pick List Picked Qty | Updating `picked_qty` in the standard Pick List can require `scripts/sync_picking_confirmations.py`. | When a warehouse user confirms picked quantities in Pick List, linked containers and shipment request statuses update immediately. | Add Pick List save hook or explicitly restrict this operation to the scanner-first page. Preferred: hook plus scanner page. | Update picked qty in Desk Pick List; assert container status/movement and shipment request status without manual processor calls. | Medium |
| LFR-05 | Test Suite Design | End-to-end validation currently calls processors directly for several flows. | Live-flow tests should prove immediate UI behavior; processor tests should separately prove recovery behavior. | Split validation into live-flow tests and processor/recovery tests. | Three packs: deployment tests, client portal tests, warehouse operation tests. Live tests must not call processors for expected immediate results. | High |
| LFR-06 | Documentation Boundaries | Some docs can imply a flow is fully immediate even when a processor is still part of the path. | Docs should clearly say what is immediate, what is processor recovery, and what remains backlog. | Update process docs after each LFR item is implemented. | Documentation review against implemented behavior. | Medium |

## Notes For Implementation

- Do not remove existing processors. They are useful for deployment, repair, and periodic reconciliation.
- Prefer small server scripts/hooks that call the existing processor functions for one document where possible.
- Avoid duplicating business logic between hooks, portal pages, and batch processors.
- After each item is implemented, run both automated validation and a browser/manual flow check with the relevant role.
