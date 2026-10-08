{
    "name": "Chebu POS UI",
    "version": "18.0.1.0.0",
    "summary": "A modern, touch-friendly visual layer for Odoo Point of Sale",
    "category": "Point of Sale",
    "author": "Chebu",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
            "chebu_pos_ui/static/src/css/pos_ui.scss",
            "chebu_pos_ui/static/src/xml/pos_ui.xml",
        ],
    },
    "installable": True,
    "application": False,
}
