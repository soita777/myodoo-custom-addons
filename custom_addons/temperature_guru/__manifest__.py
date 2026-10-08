{
    "name": "Temperature Guru",
    "version": "18.0.1.0.0",
    "summary": "Monitor cold-chain temperatures across company branches",
    "category": "Inventory/Inventory",
    "author": "Chebu",
    "license": "LGPL-3",
    "depends": ["base", "mail", "web", "chebu_inventory_movement"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/sequence.xml",
        "views/temperature_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "temperature_guru/static/src/js/temperature_dashboard.js",
            "temperature_guru/static/src/xml/temperature_dashboard.xml",
            "temperature_guru/static/src/scss/temperature_dashboard.scss",
        ],
    },
    "application": True,
    "installable": True,
}