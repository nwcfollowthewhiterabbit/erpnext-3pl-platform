import os


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def optional_env(name):
    return os.environ.get(name)


COMPANY = "3pl"
COMPANY_ABBR = "3"
COUNTRY = "Lithuania"
CURRENCY = "EUR"
LANGUAGE = "en"
TIME_ZONE = "Europe/Vilnius"
PLACEHOLDER_EMAIL = "noreply@example.invalid"

CLIENT_DESK_USER = "alpha.client@example.test"
CLIENT_DESK_PASSWORD = optional_env("CLIENT_DESK_PASSWORD")
CLIENT_DESK_CUSTOMER = "Demo Client Alpha"
CLIENT_DESK_RECEIVING_REF_PREFIX = "ALPHA-IN"
CLIENT_DESK_SHIPMENT_REF_PREFIX = "ALPHA-OUT"

WAREHOUSE_OPERATOR_USER = "warehouse.demo@example.test"
WAREHOUSE_OPERATOR_PASSWORD = optional_env("WAREHOUSE_OPERATOR_PASSWORD")
WAREHOUSE_MANAGER_USER = "warehouse.manager@example.test"
WAREHOUSE_MANAGER_PASSWORD = optional_env("WAREHOUSE_MANAGER_PASSWORD")
BUSINESS_OWNER_USER = os.environ.get("BUSINESS_OWNER_USER", "business.owner@example.test")
BUSINESS_OWNER_PASSWORD = optional_env("BUSINESS_OWNER_PASSWORD")

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

