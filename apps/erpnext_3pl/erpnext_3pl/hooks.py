app_name = "erpnext_3pl"
app_title = "ERPNext 3PL"
app_publisher = "ERPNext 3PL Platform"
app_description = "Warehouse-first 3PL extensions for ERPNext"
app_email = "noreply@example.invalid"
app_license = "MIT"

from erpnext_3pl.config.fixtures import FIXTURES as fixtures

app_include_css = ["/assets/erpnext_3pl/css/desk.css"]
app_include_js = ["/assets/erpnext_3pl/js/desk.js"]

after_install = "erpnext_3pl.install.after_install"

doc_events = {
    "Three PL Client Product": {
        "on_update": "erpnext_3pl.hooks_events.sync_client_product",
    },
    "Three PL Client Product Import": {
        "on_update": "erpnext_3pl.hooks_events.sync_product_import",
    },
    "Three PL Client Instruction": {
        "on_update": "erpnext_3pl.hooks_events.sync_client_instruction_status",
    },
    "Three PL Container": {
        "on_update": "erpnext_3pl.hooks_events.sync_container_inventory",
    },
    "Inbound Shipment Notice": {
        "before_save": "erpnext_3pl.hooks_events.sync_receiving_notice_discrepancies",
    },
    "Three PL Shipment Request": {
        "on_update": "erpnext_3pl.hooks_events.sync_shipment_request_pick_list",
    },
    "Pick List": {
        "on_update": "erpnext_3pl.hooks_events.sync_pick_list_picked",
    },
    "Stock Entry": {
        "on_submit": "erpnext_3pl.hooks_events.sync_stock_entry_flow",
    },
}

permission_query_conditions = {
    "User": "erpnext_3pl.permissions.user_query_condition",
}

has_permission = {
    "User": "erpnext_3pl.permissions.user_has_permission",
}
