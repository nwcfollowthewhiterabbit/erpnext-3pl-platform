import importlib.util
import os
import sys

import frappe


def main():
    site = sys.argv[1]
    path = sys.argv[2]
    call_main = sys.argv[3] == "1"

    os.chdir("/home/frappe/frappe-bench/sites")
    frappe.init(site=site, sites_path=".")
    frappe.connect()
    try:
        script_dir = os.path.dirname(os.path.abspath(path))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        spec = importlib.util.spec_from_file_location("project_script", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if call_main and hasattr(module, "main"):
            module.main()
        frappe.db.commit()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    main()
