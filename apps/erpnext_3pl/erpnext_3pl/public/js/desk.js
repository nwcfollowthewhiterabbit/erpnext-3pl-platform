(function () {
    var CLIENT_DESKTOP_LABELS = [
        "3PL Client",
        "Inbound",
        "Outbound",
        "Inventory",
        "Products & Issues",
    ];
    var WAREHOUSE_DESKTOP_LABELS = [
        "3PL Warehouse",
        "Warehouse Receiving",
        "Warehouse Outbound",
        "Warehouse Operations",
        "Warehouse Reports",
    ];

    function hasRole(role) {
        return (frappe.user_roles || []).indexOf(role) !== -1;
    }

    function allowedLabels() {
        if (hasRole("3PL Warehouse Manager") || hasRole("3PL Warehouse User") || hasRole("System Manager")) {
            return WAREHOUSE_DESKTOP_LABELS;
        }
        if (hasRole("3PL Client")) {
            return CLIENT_DESKTOP_LABELS;
        }
        return null;
    }

    function isDesktopRoute() {
        var route = frappe.get_route ? frappe.get_route() : null;
        return window.location.pathname === "/desk" && Array.isArray(route) && route[0] === "";
    }

    function filterDesktopIcons() {
        if (!window.frappe || !isDesktopRoute()) return;
        var allowed = allowedLabels();
        if (!allowed) return;
        var allowedSet = {};
        allowed.forEach(function (label) {
            allowedSet[label] = true;
        });
        document.querySelectorAll(".desktop-container > .icons-container > .icons > .desktop-icon").forEach(function (icon) {
            var title = icon.querySelector(".icon-title");
            var label = title ? title.textContent.trim() : "";
            icon.style.display = allowedSet[label] ? "" : "none";
        });
    }

    function scheduleFilter() {
        filterDesktopIcons();
        [100, 250, 500, 1000, 2000].forEach(function (delay) {
            setTimeout(filterDesktopIcons, delay);
        });
    }

    function bindDesktopFilter() {
        scheduleFilter();
        if (frappe.router) {
            frappe.router.on("change", scheduleFilter);
        }
        new MutationObserver(filterDesktopIcons).observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    if (window.frappe) {
        bindDesktopFilter();
    } else {
        document.addEventListener("DOMContentLoaded", function () {
            if (window.frappe) bindDesktopFilter();
        });
    }
})();
