from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = "pos.config"

    register_pool_enabled = fields.Boolean(
        string="Exclusive register",
        default=True,
        help="Only the salesperson who opened this register can use its active session.",
    )
    register_occupant_name = fields.Char(
        string="Occupied by",
        compute="_compute_register_occupancy",
    )
    register_occupant_initial = fields.Char(
        string="Occupant initial",
        compute="_compute_register_occupancy",
    )
    register_is_occupied = fields.Boolean(
        string="Occupied",
        compute="_compute_register_occupancy",
    )

    @api.depends("session_ids.state", "session_ids.user_id", "session_ids.rescue")
    def _compute_register_occupancy(self):
        for config in self:
            session = config.session_ids.filtered(
                lambda item: item.state != "closed" and not item.rescue
            )[:1]
            name = session.user_id.name if session else False
            config.register_occupant_name = name
            config.register_occupant_initial = name.strip()[:1].upper() if name else False
            config.register_is_occupied = bool(session)

    def _get_active_register_session(self):
        """Read the session after locking its config row to avoid two claims at once."""
        self.ensure_one()
        self.env.cr.execute("SELECT id FROM pos_config WHERE id = %s FOR UPDATE", [self.id])
        return self.env["pos.session"].search(
            [
                ("config_id", "=", self.id),
                ("state", "!=", "closed"),
                ("rescue", "=", False),
            ],
            limit=1,
        )

    def open_ui(self):
        """Claim a free register, or reject anyone else's active register."""
        self.ensure_one()
        if self.register_pool_enabled:
            session = self._get_active_register_session()
            if session and session.user_id != self.env.user:
                raise UserError(
                    _(
                        "%(register)s is currently in use by %(salesperson)s. "
                        "Please select another available register.",
                        register=self.name,
                        salesperson=session.user_id.name,
                    )
                )
            # ``open_ui`` below must see the session just read under the lock.
            self.invalidate_recordset(
                ["session_ids", "current_session_id", "has_active_session"]
            )
        return super().open_ui()
