COMPANY = "3pl"
COMPANY_ABBR = "3"
COUNTRY = "Lithuania"
CURRENCY = "EUR"
LANGUAGE = "en"
TIME_ZONE = "Europe/Vilnius"
PLACEHOLDER_EMAIL = "noreply@example.invalid"

CLIENT_PORTAL_USER = "alpha.client@example.test"
CLIENT_PORTAL_PASSWORD = "AlphaClient2026!"
CLIENT_PORTAL_CUSTOMER = "Demo Client Alpha"
CLIENT_PORTAL_HOME = "client/receiving-notice"

WAREHOUSE_OPERATOR_USER = "warehouse.demo@example.test"
WAREHOUSE_OPERATOR_PASSWORD = "WarehouseDemo2026!"
WAREHOUSE_MANAGER_USER = "warehouse.manager@example.test"
WAREHOUSE_MANAGER_PASSWORD = "WarehouseManager2026!"
BUSINESS_OWNER_USER = "rupusm@gmail.com"
BUSINESS_OWNER_PASSWORD = "6elz4oeiuUGAHSGRccwngNmb"

DEMO_CLIENTS = ["Demo Client Alpha", "Demo Client Beta"]

DEMO_ITEMS = [
    {
        "item_code": "SKU-ALPHA-001",
        "item_name": "Demo Alpha Widget",
        "client": "Demo Client Alpha",
        "client_sku": "ALPHA-001",
        "client_product_name": "Alpha Widget",
        "barcode": "300000000001",
    },
    {
        "item_code": "SKU-ALPHA-002",
        "item_name": "Demo Alpha Cable",
        "client": "Demo Client Alpha",
        "client_sku": "ALPHA-002",
        "client_product_name": "Alpha Cable",
        "barcode": "300000000002",
    },
    {
        "item_code": "SKU-BETA-001",
        "item_name": "Demo Beta Accessory",
        "client": "Demo Client Beta",
        "client_sku": "BETA-001",
        "client_product_name": "Beta Accessory",
        "barcode": "300000000003",
    },
]

CLIENT_PORTAL_FORMS = [
    {
        "form_name": "3PL Client Receiving Notice",
        "menu_title": "Receiving Notices",
        "route": CLIENT_PORTAL_HOME,
        "doc_type": "Inbound Shipment Notice",
        "list_title": "Receiving Notices",
        "button_label": "Submit Receiving Notice",
        "introduction_text": "Create and review receiving notices for inbound warehouse shipments.",
        "success_title": "Receiving Notice Submitted",
        "success_message": "The warehouse team can now review the expected inbound shipment.",
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "external_reference", "fieldtype": "Data", "label": "Client Notice Ref", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "expected_arrival_date", "fieldtype": "Date", "label": "Expected Arrival Date", "reqd": 1},
            {"fieldname": "portal_items_description", "fieldtype": "Small Text", "label": "Products and Quantities", "reqd": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
        ],
    },
    {
        "form_name": "3PL Client Inventory",
        "menu_title": "Inventory",
        "route": "client/inventory",
        "doc_type": "Three PL Inventory Snapshot",
        "list_title": "Inventory",
        "button_label": "View Inventory",
        "introduction_text": "Review current inventory snapshots for your products.",
        "success_title": "Inventory",
        "success_message": "",
        "allow_edit": 0,
        "allow_multiple": 0,
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "read_only": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "item_code", "fieldtype": "Link", "label": "Item", "options": "Item", "read_only": 1, "show_in_filter": 1, "allow_read_on_all_link_options": 1},
            {"fieldname": "client_sku", "fieldtype": "Data", "label": "Client SKU", "read_only": 1},
            {"fieldname": "item_name", "fieldtype": "Data", "label": "Item Name", "read_only": 1},
            {"fieldname": "qty", "fieldtype": "Float", "label": "Qty", "read_only": 1},
            {"fieldname": "uom", "fieldtype": "Link", "label": "UOM", "options": "UOM", "read_only": 1, "allow_read_on_all_link_options": 1},
            {"fieldname": "warehouse", "fieldtype": "Link", "label": "Location", "options": "Warehouse", "read_only": 1, "allow_read_on_all_link_options": 1},
            {"fieldname": "container_code", "fieldtype": "Link", "label": "Container / Box", "options": "Three PL Container", "read_only": 1, "allow_read_on_all_link_options": 1},
            {"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Available\nReceiving\nHold\nAllocated\nShipped", "read_only": 1},
        ],
    },
    {
        "form_name": "3PL Client Shipment Request",
        "menu_title": "Shipment Requests",
        "route": "client/shipment-request",
        "doc_type": "Three PL Shipment Request",
        "list_title": "Shipment Requests",
        "button_label": "Submit Shipment Request",
        "introduction_text": "Create outbound shipment requests for products stored in the warehouse.",
        "success_title": "Shipment Request Submitted",
        "success_message": "The warehouse team can now review and start picking.",
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "external_reference", "fieldtype": "Data", "label": "Client Shipment Ref", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "requested_ship_date", "fieldtype": "Date", "label": "Requested Ship Date", "reqd": 1},
            {"fieldname": "destination_name", "fieldtype": "Data", "label": "Destination Name", "reqd": 1},
            {"fieldname": "destination_address", "fieldtype": "Small Text", "label": "Destination Address", "reqd": 1},
            {"fieldname": "portal_items_description", "fieldtype": "Small Text", "label": "Products and Quantities", "reqd": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
        ],
    },
    {
        "form_name": "3PL Client Discrepancy Instruction",
        "menu_title": "Discrepancy Instructions",
        "route": "client/discrepancy-instruction",
        "doc_type": "Three PL Client Instruction",
        "list_title": "Discrepancy Instructions",
        "button_label": "Submit Instruction",
        "introduction_text": "Send warehouse instructions for receiving discrepancies.",
        "success_title": "Instruction Submitted",
        "success_message": "The warehouse team can now review your instruction.",
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "receiving_notice", "fieldtype": "Link", "label": "Receiving Notice", "options": "Inbound Shipment Notice", "reqd": 1, "show_in_filter": 1, "allow_read_on_all_link_options": 1},
            {"fieldname": "item_code", "fieldtype": "Link", "label": "Item", "options": "Item", "allow_read_on_all_link_options": 1},
            {"fieldname": "client_sku", "fieldtype": "Data", "label": "Client SKU"},
            {"fieldname": "instruction_type", "fieldtype": "Select", "label": "Instruction Type", "options": "Accept Difference\nReturn Goods\nHold For Review\nDispose Damaged Goods\nOther", "reqd": 1},
            {"fieldname": "instruction_text", "fieldtype": "Small Text", "label": "Instruction", "reqd": 1},
        ],
    },
]

CLIENT_PORTAL_ROUTES = {form["form_name"]: (form["route"], {field["fieldname"] for field in form["fields"]}) for form in CLIENT_PORTAL_FORMS}
