{
    "name": "My Arena",
    "summary": "A private notebook for every user.",
    "description": """
My Arena gives each Odoo user a personal notebook for notes, ideas, tasks, and reminders.
Users can only access their own notes.
    """,
    "version": "18.0.1.0.0",
    "category": "Productivity",
    "author": "Chebu",
    "website": "",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/my_arena_security.xml",
        "security/ir.model.access.csv",
        "views/my_arena_note_views.xml",
        "views/my_arena_menus.xml",
    ],
    "images": ["static/description/icon.png"],
    "application": True,
    "installable": True,
}
