from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ChebuPosRegister(models.Model):
    _name = "chebu.pos.register"
    _description = "Chebu POS Register"
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, copy=False, tracking=True)
    register_type = fields.Selection(
        [("cashier", "Cashier"), ("sales", "Sales")],
        required=True,
        default="cashier",
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        tracking=True,
    )
    pos_config_id = fields.Many2one("pos.config", string="POS Configuration")
    user_id = fields.Many2one("res.users", string="Assigned User", tracking=True)
    session_id = fields.Many2one("pos.session", string="POS Session", tracking=True)
    status = fields.Selection(
        [("available", "Available"), ("active", "Active"), ("locked", "Locked")],
        default="available",
        required=True,
        tracking=True,
    )
    last_login = fields.Datetime()
    last_logout = fields.Datetime()

    _sql_constraints = [
        ("chebu_register_code_unique", "unique(code)", "Register code must be unique."),
    ]

    @api.constrains("status", "user_id")
    def _check_register_status(self):
        for record in self:
            if record.status == "active" and not record.user_id:
                raise UserError(_("An active register must have an assigned user."))
            if record.user_id and record.status == "available":
                raise UserError(
                    _("A register in use cannot be marked available while still assigned to a user.")
                )

    def _serialize(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "register_type": self.register_type,
            "register_type_label": dict(self._fields["register_type"].selection).get(
                self.register_type, self.register_type
            ),
            "status": self.status,
            "status_label": dict(self._fields["status"].selection).get(
                self.status, self.status
            ),
            "active": self.active,
            "user_id": self.user_id.id if self.user_id else False,
            "user_name": self.user_id.name if self.user_id else "",
            "session_id": self.session_id.id if self.session_id else False,
            "session_name": self.session_id.name if self.session_id else "",
            "pos_config_id": self.pos_config_id.id if self.pos_config_id else False,
            "pos_config_name": self.pos_config_id.name if self.pos_config_id else "",
        }

    @api.model
    def get_registers_for_pos(self):
        return [record._serialize() for record in self.search([("active", "=", True)])]

    @api.model
    def claim_register(self, register_id, user_id=None, session_id=None):
        register = self.browse(int(register_id))
        if not register:
            raise UserError(_("Register not found."))
        if not register.active:
            raise UserError(_("Register is currently unavailable."))
        if register.status == "locked":
            raise UserError(_("Register is locked and cannot be opened."))

        user = self.env["res.users"].browse(int(user_id)) if user_id else self.env.user
        if not user:
            raise UserError(_("No user was supplied to claim this register."))

        if register.user_id and register.user_id.id != user.id and register.status == "active":
            raise UserError(_("Register already in use by %s.") % register.user_id.name)

        if register.user_id and register.user_id.id == user.id and register.status == "active":
            if session_id:
                register.session_id = int(session_id)
            register.last_login = fields.Datetime.now()
            return {"success": True, "register": register._serialize()}

        register.user_id = user.id
        register.status = "active"
        register.last_login = fields.Datetime.now()
        if session_id:
            register.session_id = int(session_id)
        return {"success": True, "register": register._serialize()}

    @api.model
    def release_register(self, register_id, user_id=None):
        register = self.browse(int(register_id))
        if not register:
            raise UserError(_("Register not found."))

        if user_id and register.user_id and register.user_id.id != int(user_id):
            raise UserError(_("You cannot close another user's register."))

        register.user_id = False
        register.session_id = False
        register.status = "available"
        register.last_logout = fields.Datetime.now()
        return {"success": True, "register": register._serialize()}
