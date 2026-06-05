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
- Basic lifecycle fields are defined.
- Demo containers exist.
- Reports show containers.

Open:

- real location naming convention;
- repack workflow;
- container movement history;
- scanner/mobile UX;
- automatic inventory snapshot updates.

## Handling Units

Status: base model implemented.

Client question:

> Is there a possibility to enter Handling Units in ERPNext, or does this functionality need to be created?

Answer:

ERPNext has standard stock entities, but not a complete 3PL Handling Unit workflow. This project implements that missing WMS layer as `Three PL Container`, while keeping ERPNext stock movement logic as the base.
