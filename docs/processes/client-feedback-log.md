# Client Feedback Log

This file tracks decisions and open points from client conversations.

## Warehouse Locations And Boxes

Status: decision captured.

Decision:

- Warehouse locations are stable physical places.
- Boxes, cartons, and pallets are Handling Units.
- Handling Units are modeled through `Three PL Container`.
- Boxes should not be created as ERPNext `Warehouse` records.

Implemented:

- `Three PL Container` exists.
- `Three PL Container Move` exists.
- `Three PL Container Repack` exists.
- Basic lifecycle fields are defined.
- Demo containers exist.
- `Three PL Container Movement` exists.
- Demo applied move operation exists as `MOVE-ALPHA-001`.
- Demo applied repack operation exists as `REPACK-ALPHA-001`.
- Demo received and putaway movement records exist.
- Reports show containers.
- Reports show container move operations.
- Reports show container repack operations.
- Reports show container movement history.

Open:

- real location naming convention;
- advanced split/merge validation;
- submit-time automation for move/repack operations;
- scanner/mobile UX;
- automatic inventory snapshot updates.

Latest client feedback:

- The client started entering the warehouse location structure.
- The client could not rename warehouse locations.
- This is a setup-phase blocker because the location naming scheme is still being refined.

Decision:

- Warehouse location renaming should stay disabled for normal warehouse roles.
- Renaming a warehouse location is an administrative/setup operation.
- Boxes still must not be modeled as warehouse locations.
- Once real stock transactions are actively running, renaming already-used locations should be handled carefully and documented as an administrative operation.

Implementation note:

- ERPNext `Warehouse` has rename disabled by default.
- The deployment configuration keeps `Warehouse.allow_rename` disabled through a versioned Property Setter.

## MVP Flow Scope From Client

Status: captured for roadmap.

Client requested these first working flows:

- user roles;
- receiving products: client enters, warehouse receives, compares, and confirms;
- moving products between warehouse locations;
- sending orders: client enters an order, warehouse picks, prepares, and sends;
- warehouse corrections for wrong quantities in boxes or similar issues;
- inventory / stocktake.

Requested reports:

- product balance on a selected day for the client;
- warehouse operation turnover for a selected period for client and warehouse users.

Current interpretation:

- Roles are implemented.
- Receiving is implemented as an MVP with required inbound receipt context, scanner support for expected/unexpected items, condition capture, received quantity sync, variance calculation, and discrepancy rows.
- Location movement is implemented for containers and scanner-first container moves.
- Shipment requests are implemented as portal MVP records and create draft Pick Lists for structured item rows. Scanner-first picking confirmation marks containers as picked. Submitted packing/shipping Stock Entries update request and container statuses. Carrier integrations and polished shipment tracking remain open.
- Corrections, correction stock posting, correction review, stocktake, full-container repack, and partial split are implemented as MVP flows.
- Inventory snapshot reports, date-based balance, and period operation turnover reports exist as MVP reports.

Implementation note:

- Invalid container repack drafts are treated as correction records that need manual review.
- The automatic repack processor must not stop deployment because of user-entered quantity mismatches.
- Such repacks are moved to `Needs Review` with the validation message in notes.

## Handling Units

Status: base model implemented.

Client question:

> Is there a possibility to enter Handling Units in ERPNext, or does this functionality need to be created?

Answer:

ERPNext has standard stock entities, but not a complete 3PL Handling Unit workflow. This project implements that missing WMS layer as `Three PL Container`, while keeping ERPNext stock movement logic as the base.
