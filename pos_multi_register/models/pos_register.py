from odoo import fields, models


class PosRegister(models.Model):
    _name = "pos.register"
    _description = "POS Register"
    _order = "name"

    name = fields.Char(
        string="Register Name",
        required=True,
        copy=False,
    )

    code = fields.Char(
        string="Register Code",
        required=True,
        copy=False,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

    branch = fields.Char(
        string="Branch",
        required=True,
    )

    description = fields.Text(
        string="Description",
    )

    state = fields.Selection(
        [
            ("available", "Available"),
            ("occupied", "Occupied"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="available",
        required=True,
    )

    _sql_constraints = [
        (
            "register_code_unique",
            "unique(code)",
            "Register code must be unique.",
        ),
    ]
