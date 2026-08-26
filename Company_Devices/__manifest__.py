{
    "name": "Company Devices",
    "summary": "Track company devices and employee assignments.",
    "description": """
Company Devices keeps an inventory of company laptops, phones, tablets,
desktops, and other equipment. Track asset numbers, serial numbers,
assignments, remote management, tracking methods, locations, and warranty
information in one place.
    """,
    "version": "18.0.1.0.0",
    "category": "Operations",
    "author": "Chebu",
    "license": "LGPL-3",
    "depends": ["base", "hr"],
    "data": [
        "security/company_device_security.xml",
        "security/ir.model.access.csv",
        "views/company_device_views.xml",
    ],
    "application": True,
    "installable": True,
}
