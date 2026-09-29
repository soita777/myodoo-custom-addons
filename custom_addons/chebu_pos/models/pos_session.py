from odoo import fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    chebu_register_id = fields.Many2one("chebu.pos.register", string="Chebu Register")
