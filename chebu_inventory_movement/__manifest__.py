{
    "name": "Inventory Movement & Delivery Management",
    "version": "18.0.1.0.0",
    "summary": "Trace stock movements and manage deliveries end to end",
    "description": """
Inventory Movement & Delivery Management provides an append-only movement
ledger, branch dimensions, configurable approvals, and delivery planning on top
of standard Odoo inventory transactions.
    """,
    "category": "Inventory/Inventory",
    "author": "Chebu",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "stock",
        "product",
        "uom",
        "contacts",
        "sale_management",
        "purchase",
        "point_of_sale",
        "account",
        "delivery",
        "fleet",
        "hr",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/sequence.xml",
        "views/branch_views.xml",
        "views/ledger_views.xml",
        "views/approval_views.xml",
        "views/delivery_views.xml",
        "views/dashboard_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
}
