from odoo import fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    chebu_register_id = fields.Many2one("chebu.pos.register", string="Chebu Register")

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "closed":
            registers = self.env["chebu.pos.register"].search([("session_id", "in", self.ids)])
            for register in registers:
                register.sudo().write(
                    {
                        "user_id": False,
                        "session_id": False,
                        "status": "locked" if register.status == "locked" else "available",
                        "last_logout": fields.Datetime.now(),
                    }
                )
        return result
