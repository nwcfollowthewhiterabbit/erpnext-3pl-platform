# Warehouse Locations

## Business Decision

ERPNext `Warehouse` records should model stable physical locations only:

- receiving areas;
- inspection areas;
- zones;
- aisles;
- racks;
- shelves;
- bins / cells.

Boxes, cartons, and pallets should not be modeled as warehouse locations. They are Handling Units and belong in `Three PL Container`.

## Reason

A location is a stable physical place. A box is temporary and may be:

- replaced;
- merged with another box;
- split into multiple boxes;
- emptied;
- closed;
- moved onto a pallet;
- shipped out.

ERPNext protects used warehouse locations from deletion after stock transactions. If every cardboard box becomes a warehouse location, the warehouse tree becomes noisy and hard to maintain.

## Recommended Naming Convention

Use a compact location code:

`ZONE-AISLE-RACK-SHELF-BIN`

Examples:

- `A-01-R01-S02-B03`
- `A-01-R01-S02-B04`
- `B-02-R03-S01-B01`

The exact depth should be agreed with the client before importing the real warehouse tree.

## Current Implementation

Seed locations:

- `Receiving Area - 3`
- `Temporary Receiving - 3`
- `Inspection and Comparison - 3`
- `Storage Locations - 3`
- `Aisle A - 3`
- `Aisle B - 3`
- `Overflow - 3`
- `Packing - 3`
- `Shipping - 3`

These are enough for demo and MVP flow validation. They are not intended to be the final physical warehouse map.

## Remaining Decisions

- Exact hierarchy depth: zone -> aisle -> rack -> shelf -> bin.
- Whether one bin may contain multiple clients.
- Whether one bin may contain multiple SKUs.
- Whether fixed locations or dynamic putaway will be used.
- Label format for locations and containers.
- Import format for the real warehouse tree.

## Client Feedback Wording

The client can start preparing the warehouse location map now. We should agree the naming convention and hierarchy depth before entering it into ERPNext. Locations should represent stable physical places, while boxes and pallets should be represented separately as Handling Units / `Three PL Container`.
