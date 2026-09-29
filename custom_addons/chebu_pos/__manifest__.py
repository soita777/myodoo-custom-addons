{
    "name": "Chebu POS",
    "version": "18.0.1.0.0",
    "summary": "Chebu POS register orchestration and modern login flow",
    "category": "Point of Sale",
    "author": "Chebu",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/chebu_pos_register_data.xml",
        "views/chebu_pos_register_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "chebu_pos/static/src/js/chebu_pos_register.js",
            "chebu_pos/static/src/xml/chebu_pos_register.xml",
            "chebu_pos/static/src/scss/chebu_pos_register.scss",
        ],
    },
    "installable": True,
    "application": False,
}
