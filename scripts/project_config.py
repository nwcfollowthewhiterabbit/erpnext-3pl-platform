import os


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


COMPANY = "3pl"
COMPANY_ABBR = "3"
COUNTRY = "Lithuania"
CURRENCY = "EUR"
LANGUAGE = "en"
TIME_ZONE = "Europe/Vilnius"
PLACEHOLDER_EMAIL = "noreply@example.invalid"

CLIENT_PORTAL_USER = "alpha.client@example.test"
CLIENT_PORTAL_PASSWORD = required_env("CLIENT_PORTAL_PASSWORD")
CLIENT_PORTAL_CUSTOMER = "Demo Client Alpha"
CLIENT_PORTAL_RECEIVING_ROUTE = "client/receiving-notice"
CLIENT_PORTAL_HOME = f"{CLIENT_PORTAL_RECEIVING_ROUTE}/list"
CLIENT_PORTAL_RECEIVING_REF_PREFIX = "ALPHA-IN"
CLIENT_PORTAL_SHIPMENT_REF_PREFIX = "ALPHA-OUT"

WAREHOUSE_OPERATOR_USER = "warehouse.demo@example.test"
WAREHOUSE_OPERATOR_PASSWORD = required_env("WAREHOUSE_OPERATOR_PASSWORD")
WAREHOUSE_MANAGER_USER = "warehouse.manager@example.test"
WAREHOUSE_MANAGER_PASSWORD = required_env("WAREHOUSE_MANAGER_PASSWORD")
BUSINESS_OWNER_USER = os.environ.get("BUSINESS_OWNER_USER", "business.owner@example.test")
BUSINESS_OWNER_PASSWORD = required_env("BUSINESS_OWNER_PASSWORD")

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
        "item_code": "SKU-ALPHA-003",
        "item_name": "Demo Alpha Adapter",
        "client": "Demo Client Alpha",
        "client_sku": "ALPHA-003",
        "client_product_name": "Alpha Adapter",
        "barcode": "300000000004",
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
        "route": CLIENT_PORTAL_RECEIVING_ROUTE,
        "doc_type": "Inbound Shipment Notice",
        "list_title": "Receiving Notices",
        "button_label": "Submit Receiving Notice",
        "introduction_text": "Create and review receiving notices for inbound warehouse shipments.",
        "success_title": "Receiving Notice Submitted",
        "success_message": "The warehouse team can now review the expected inbound shipment.",
        "client_script": """
(function () {
  var FALLBACK_CUSTOMER = "__CLIENT_PORTAL_CUSTOMER__";
  var REF_PREFIX = "__CLIENT_PORTAL_RECEIVING_REF_PREFIX__";

  function pad(value, width) {
    return String(value).padStart(width, '0');
  }

  function todayStamp() {
    var now = new Date();
    return String(now.getFullYear()) + pad(now.getMonth() + 1, 2) + pad(now.getDate(), 2);
  }

  function getFieldValue(fieldname) {
    if (window.frappe && frappe.web_form && frappe.web_form.get_value) {
      return frappe.web_form.get_value(fieldname);
    }
    var input = document.querySelector('[data-fieldname="' + fieldname + '"] input, [name="' + fieldname + '"], input[data-fieldname="' + fieldname + '"]');
    return input ? input.value : '';
  }

  function setFieldValue(fieldname, value) {
    if (window.frappe && frappe.web_form && frappe.web_form.set_value) {
      frappe.web_form.set_value(fieldname, value);
      return;
    }
    var input = document.querySelector('[data-fieldname="' + fieldname + '"] input, [name="' + fieldname + '"], input[data-fieldname="' + fieldname + '"]');
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  function api(method, args) {
    var body = new URLSearchParams();
    Object.keys(args || {}).forEach(function (key) {
      var value = args[key];
      body.set(key, typeof value === 'string' ? value : JSON.stringify(value));
    });
    return fetch('/api/method/' + method, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body
    }).then(function (response) {
      return response.json().then(function (payload) {
        if (!response.ok) throw new Error(payload.exception || payload._error_message || ('Request failed: ' + response.status));
        return payload;
      });
    });
  }

  function nextReference(existingRows, basePrefix) {
    var maxNumber = 0;
    (existingRows || []).forEach(function (row) {
      var ref = row.external_reference || '';
      if (ref.indexOf(basePrefix + '-') !== 0) return;
      var suffix = ref.slice(basePrefix.length + 1);
      var parsed = parseInt(suffix, 10);
      if (!Number.isNaN(parsed)) maxNumber = Math.max(maxNumber, parsed);
    });
    return basePrefix + '-' + pad(maxNumber + 1, 3);
  }

  function installAutoReference() {
    if (getFieldValue('external_reference')) return;

    var datePart = todayStamp();
    var basePrefix = REF_PREFIX + '-' + datePart;
    var customer = getFieldValue('customer') || FALLBACK_CUSTOMER;

    api('frappe.client.get_list', {
      doctype: 'Inbound Shipment Notice',
      filters: {
        customer: customer,
        external_reference: ['like', basePrefix + '-%']
      },
      fields: ['external_reference'],
      limit_page_length: 100,
      order_by: 'external_reference desc'
    }).then(function (response) {
      if (getFieldValue('external_reference')) return;
      setFieldValue('external_reference', nextReference(response.message || [], basePrefix));
    }).catch(function () {
      if (!getFieldValue('external_reference')) {
        setFieldValue('external_reference', basePrefix + '-001');
      }
    });
  }

  if (window.frappe && frappe.ready) {
    frappe.ready(function () { setTimeout(installAutoReference, 250); });
  } else {
    document.addEventListener('DOMContentLoaded', function () { setTimeout(installAutoReference, 250); });
  }
})();
"""
        .replace("__CLIENT_PORTAL_CUSTOMER__", CLIENT_PORTAL_CUSTOMER)
        .replace("__CLIENT_PORTAL_RECEIVING_REF_PREFIX__", CLIENT_PORTAL_RECEIVING_REF_PREFIX),
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "external_reference", "fieldtype": "Data", "label": "Client Notice Ref", "reqd": 1, "show_in_filter": 1, "description": "Auto-filled as CLIENT-IN-YYYYMMDD-###. You may replace it with your own PO, ASN, invoice, or shipment reference."},
            {"fieldname": "expected_arrival_date", "fieldtype": "Date", "label": "Expected Arrival Date", "reqd": 1},
            {"fieldname": "portal_items_description", "fieldtype": "Small Text", "label": "Products and Quantities", "reqd": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
        ],
    },
    {
        "form_name": "3PL Client Product",
        "menu_title": "Products",
        "route": "client/products",
        "doc_type": "Three PL Client Product",
        "list_title": "Products",
        "button_label": "Save Product",
        "introduction_text": "Create and maintain your product cards. The warehouse system syncs approved fields into ERPNext Items.",
        "success_title": "Product Saved",
        "success_message": "The product card was saved and will be synchronized with the warehouse item master.",
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "client_sku", "fieldtype": "Data", "label": "Client SKU", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "product_name", "fieldtype": "Data", "label": "Product Name", "reqd": 1},
            {"fieldname": "product_description", "fieldtype": "Small Text", "label": "Description"},
            {"fieldname": "uom", "fieldtype": "Link", "label": "UOM", "options": "UOM", "reqd": 1, "default": "Nos", "allow_read_on_all_link_options": 1},
            {"fieldname": "barcode", "fieldtype": "Data", "label": "Barcode"},
            {"fieldname": "product_image", "fieldtype": "Attach Image", "label": "Photo"},
            {"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nInactive", "default": "Active", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "item_code", "fieldtype": "Link", "label": "ERPNext Item", "options": "Item", "read_only": 1, "allow_read_on_all_link_options": 1},
            {"fieldname": "sync_status", "fieldtype": "Select", "label": "Sync Status", "options": "Pending\nSynced\nFailed", "read_only": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
        ],
    },
    {
        "form_name": "3PL Client Product Import",
        "menu_title": "Product Imports",
        "route": "client/product-import",
        "doc_type": "Three PL Client Product Import",
        "list_title": "Product Imports",
        "button_label": "Upload Product File",
        "introduction_text": "Upload an Excel or CSV product file for controlled product card creation and updates.",
        "success_title": "Product Import Uploaded",
        "success_message": "The file was uploaded and will be processed by the warehouse product sync.",
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "hidden": 1, "default": CLIENT_PORTAL_CUSTOMER, "allow_read_on_all_link_options": 1},
            {"fieldname": "import_file", "fieldtype": "Attach", "label": "Excel / CSV File", "reqd": 1},
            {"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Pending\nApplied\nFailed", "default": "Pending", "read_only": 1, "show_in_filter": 1},
            {"fieldname": "rows_total", "fieldtype": "Int", "label": "Rows Total", "read_only": 1},
            {"fieldname": "rows_applied", "fieldtype": "Int", "label": "Rows Applied", "read_only": 1},
            {"fieldname": "error_log", "fieldtype": "Small Text", "label": "Error Log", "read_only": 1},
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
