from erpnext_3pl.config.workflows import MVP_WORKFLOWS


PROJECT_DOCTYPES = [
    "Inbound Shipment Notice",
    "Inbound Shipment Notice Item",
    "Inbound Shipment Discrepancy",
    "Three PL Container",
    "Three PL Container Item",
    "Three PL Container Move",
    "Three PL Container Movement",
    "Three PL Container Repack",
    "Three PL Repack Source",
    "Three PL Repack Item",
    "Three PL Warehouse Correction",
    "Three PL Stocktake Session",
    "Three PL Stocktake",
    "Three PL Inventory Snapshot",
    "Three PL Inventory Balance Snapshot",
    "Three PL Client Product",
    "Three PL Client Product Change Log",
    "Three PL Client Product Import",
    "Three PL Shipment Request",
    "Three PL Shipment Request Item",
    "Three PL Client Instruction",
]

PROJECT_ROLES = [
    "3PL Client",
    "3PL Warehouse Manager",
    "3PL Warehouse User",
]

PROJECT_CUSTOM_FIELDS = [
    "Item-client_product_name",
    "Item-client_sku",
    "Item-owner_client",
    "Item-three_pl_ownership_section",
    "Pick List-client",
    "Pick List-client_section",
    "Pick List-container_code",
    "Pick List-shipment_reference",
    "Pick List-shipment_request",
    "Pick List Item-container_code",
    "Pick List Item-scanned_location",
    "Stock Entry-client",
    "Stock Entry-client_section",
    "Stock Entry-container_code",
    "Stock Entry-inbound_shipment_notice",
    "Stock Entry-scanned_location",
    "Stock Entry-shipment_reference",
    "Stock Entry-shipment_request",
    "Stock Entry-warehouse_correction",
    "Stock Entry-warehouse_flow",
    "Stock Entry Detail-container_code",
    "Stock Entry Detail-scanned_location",
]

PROJECT_STOCK_ENTRY_TYPES = [
    "3PL Inbound Receipt",
    "3PL Comparison",
    "3PL Put Away",
    "3PL Internal Movement",
    "3PL Quantity Gain",
    "3PL Quantity Loss",
    "3PL Packing",
    "3PL Shipping",
]

PROJECT_REPORTS = [
    "3PL ASN vs Received",
    "3PL Client Inventory",
    "3PL Client Inventory Summary",
    "3PL Container Movements",
    "3PL Container Moves",
    "3PL Container Repacks",
    "3PL Containers",
    "3PL Corrections Needing Review",
    "3PL Inventory Balance By Date",
    "3PL Receiving Discrepancies",
    "3PL Shipment Requests",
    "3PL Stocktake Sessions",
    "3PL Stocktakes",
    "3PL Warehouse Corrections",
    "3PL Warehouse Operation Turnover",
]

PROJECT_MODULE_PROFILES = [
    "Warehouse Only",
    "3PL Client Only",
]

PROJECT_WORKFLOWS = [workflow["name"] for workflow in MVP_WORKFLOWS]
PROJECT_WORKFLOW_STATES = sorted({state for workflow in MVP_WORKFLOWS for state in workflow["states"]})
PROJECT_WORKFLOW_ACTIONS = sorted(
    {transition[1] for workflow in MVP_WORKFLOWS for transition in workflow["transitions"]}
)


FIXTURES = [
    {"dt": "Custom Field", "filters": [["name", "in", PROJECT_CUSTOM_FIELDS]]},
    {"dt": "Custom DocPerm", "filters": [["role", "in", PROJECT_ROLES]]},
    {"dt": "Role", "filters": [["name", "in", PROJECT_ROLES]]},
    {"dt": "Module Profile", "filters": [["name", "in", PROJECT_MODULE_PROFILES]]},
    {"dt": "Stock Entry Type", "filters": [["name", "in", PROJECT_STOCK_ENTRY_TYPES]]},
    {"dt": "Report", "filters": [["name", "in", PROJECT_REPORTS]]},
    {"dt": "Workflow", "filters": [["name", "in", PROJECT_WORKFLOWS]]},
    {"dt": "Workflow State", "filters": [["name", "in", PROJECT_WORKFLOW_STATES]]},
    {"dt": "Workflow Action Master", "filters": [["name", "in", PROJECT_WORKFLOW_ACTIONS]]},
    {
        "dt": "Web Page",
        "filters": [["route", "like", "warehouse/%"]],
    },
    {
        "dt": "Property Setter",
        "filters": [["doc_type", "=", "Warehouse"], ["property", "=", "allow_rename"]],
    },
]
