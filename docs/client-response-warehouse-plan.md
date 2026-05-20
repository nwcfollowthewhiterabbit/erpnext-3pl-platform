# Warehouse Configuration Plan

We will move in stages.

## 1. Warehouse Flows

First we will formalize the core warehouse flows that can be implemented immediately on top of standard ERPNext logic and that match the described processes:

- Receiving
- Putaway
- Picking / Pick List
- Packing
- Dispatch

## 2. Warehouse-Only Interface

We will prepare the system structure for warehouse-only usage:

- hide unrelated ERP modules and entities from the interface;
- keep only warehouse operations and related flows visible;
- preserve compatibility with the standard ERPNext architecture so the system can be extended later without a large departure from default logic.

## 3. Test Flow and Demo Structure

We will prepare a test flow and demo structure:

- warehouse locations;
- barcode flow;
- example receiving and picking process;
- demo SKU records and warehouse movements.

## 4. Test Access and Manual

After that we will send access to the test system with a short description:

- what processes are already configured;
- how the current flow works;
- where to go inside the system;
- where the corresponding sections and manual flow are located.

## Open Questions

The next details to clarify are:

- Will separate scanner devices be used, or is browser plus barcode scanner enough for the first stage?
- Is multi-client inventory ownership required?
- Are serial numbers, batch numbers, or expiry dates required?
- Should storage be fixed-location or dynamic putaway?
- Will courier or shipping system integrations be needed later?
- Should the primary warehouse workflow be mobile/scanner-first?
