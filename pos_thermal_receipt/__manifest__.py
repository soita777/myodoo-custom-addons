{
    "name": "POS Thermal Receipt",
    "summary": "Format Point of Sale receipts for 80 mm thermal printers",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "author": "Chebu",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_thermal_receipt/static/src/scss/thermal_receipt.scss",
        ],
    },
    "installable": True,
    "application": False,
}
