{
    "name": "Fleet",
    "summary": "Track company vehicles, assignments, and compliance.",
    "description": """
Fleet keeps a register of company vehicles and other transport
resources. Track ownership, assignment, availability, registration,
insurance, servicing, mileage, and operational notes in one place.
    """,
    "version": "18.0.1.0.0",
    "category": "Operations",
    "author": "Chebu",
    "license": "LGPL-3",
    "icon": "static/description/icon.svg",
    "depends": ["base", "hr"],
    "data": [
        "security/company_transport_security.xml",
        "security/ir.model.access.csv",
        "views/company_transport_views.xml",
    ],
    "application": True,
    "installable": True,
}
