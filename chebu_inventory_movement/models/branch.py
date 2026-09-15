from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InventoryBranch(models.Model):
    _name = "chebu.inventory.branch"
    _description = "Inventory Operating Branch"
    _order = "company_id, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    partner_id = fields.Many2one("res.partner", string="Branch Contact")
    manager_id = fields.Many2one("res.users", string="Branch Manager")
    warehouse_ids = fields.One2many("stock.warehouse", "chebu_branch_id", string="Warehouses")
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        (
            "company_code_unique",
            "UNIQUE(company_id, code)",
            "Branch code must be unique per company.",
        ),
    ]

    @api.constrains("code")
    def _check_code(self):
        for branch in self:
            if branch.code != branch.code.strip().upper():
                raise ValidationError("Branch codes must be uppercase without surrounding spaces.")


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    chebu_branch_id = fields.Many2one(
        "chebu.inventory.branch", string="Operating Branch", index=True
    )
