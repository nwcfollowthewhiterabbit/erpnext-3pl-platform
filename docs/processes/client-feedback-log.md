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

Status: base Desk flow implemented; bulk import moved outside MVP1.

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
- Shipment requests are implemented as Desk-native MVP records and create draft Pick Lists for structured item rows. Scanner-first picking confirmation marks containers as picked. Submitted packing/shipping Stock Entries update request and container statuses. Carrier integrations and polished shipment tracking remain open.
- Corrections, correction stock posting, correction review, and stocktake are implemented as MVP flows. Full-container repack and partial split are available as extended warehouse support, not as required MVP1 acceptance flows.
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

## Stage MVP2 Product Card Management

Status: MVP2 base implemented.

Client feedback:

> Important functionality: product card management. New products are created and old products are updated by the client, so this functionality needs to be added. Ideally this should also support Excel export/import. Each product should have a photo.

Current interpretation:

- This is part of Stage MVP2 because it changes client-facing master data management.
- The base Desk flow is implemented as `Three PL Client Product` in the existing client Desk.
- The product record should stay based on ERPNext `Item`.
- The 3PL business identity should remain `Owner Client + Client SKU`.
- The client should manage products through a constrained client Desk flow.
- Product photos should be attached to the item/product card.
- Product Export is available for review/reporting. Bulk Product Import is outside MVP1 and remains a post-MVP1/admin roadmap capability, not a required client flow.
- Client delete is implemented as deactivate/soft-delete, preserving ERPNext item and stock history.
- Client product changes are recorded in `Three PL Client Product Change Log`.

Open:

- final required fields for product cards;
- product approval workflow before warehouse use;
- whether clients can reactivate inactive products;
- whether any future CSV/XLSX import flow needs an approval step before products become active.
