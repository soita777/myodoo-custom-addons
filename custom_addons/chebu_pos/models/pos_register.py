from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


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
    currency_id = fields.Many2one(related="company_id.currency_id")
    order_count = fields.Integer(compute="_compute_sales_dashboard")
    today_order_count = fields.Integer(compute="_compute_sales_dashboard")
    today_collection = fields.Monetary(compute="_compute_sales_dashboard", currency_field="currency_id")
    total_collection = fields.Monetary(compute="_compute_sales_dashboard", currency_field="currency_id")
    recent_order_ids = fields.Many2many("pos.order", compute="_compute_sales_dashboard")
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

    @api.depends("session_id", "company_id")
    def _compute_sales_dashboard(self):
        pos_orders = self.env["pos.order"]
        paid_states = ["paid", "done", "invoiced"]
        for register in self:
            base_domain = [
                ("session_id.chebu_register_id", "=", register.id),
                ("state", "in", paid_states),
            ]
            register.order_count = pos_orders.search_count(base_domain)
            totals = pos_orders.read_group(base_domain, ["amount_total:sum"], [])
            register.total_collection = totals[0].get("amount_total", 0.0) if totals else 0.0

            today = fields.Date.context_today(register)
            timezone = pytz.timezone(
                self.env.context.get("tz") or self.env.user.tz or "UTC"
            )
            start_local = timezone.localize(datetime.combine(today, time.min))
            end_local = timezone.localize(datetime.combine(today + timedelta(days=1), time.min))
            today_domain = base_domain + [
                ("date_order", ">=", start_local.astimezone(pytz.UTC).replace(tzinfo=None)),
                ("date_order", "<", end_local.astimezone(pytz.UTC).replace(tzinfo=None)),
            ]
            register.today_order_count = pos_orders.search_count(today_domain)
            today_totals = pos_orders.read_group(today_domain, ["amount_total:sum"], [])
            register.today_collection = (
                today_totals[0].get("amount_total", 0.0) if today_totals else 0.0
            )
            register.recent_order_ids = pos_orders.search(
                base_domain, order="date_order desc, id desc", limit=10
            )

    @api.model
    def get_registers_for_pos(self):
        return [record._serialize() for record in self.search([("active", "=", True)])]

    @api.model
    def claim_register(self, register_id, user_id=None, session_id=None):
        register = self.browse(int(register_id)).exists()
        if not register:
            raise UserError(_("Register not found."))
        if not register.active:
            raise UserError(_("Register is currently unavailable."))
        if register.status == "locked":
            raise UserError(_("Register is locked and cannot be opened."))

        user = self.env["res.users"].browse(int(user_id)) if user_id else self.env.user
        if not user:
            raise UserError(_("No user was supplied to claim this register."))
        if user != self.env.user and not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise AccessError(_("You can only open a register for your own user."))

        session = self.env["pos.session"]
        if session_id:
            session = self.env["pos.session"].browse(int(session_id)).exists()
            if not session:
                raise UserError(_("POS session not found."))
            if register.pos_config_id and session.config_id != register.pos_config_id:
                raise UserError(_("This register is assigned to a different POS configuration."))
            if session.chebu_register_id and session.chebu_register_id != register:
                raise UserError(_("This POS session is already assigned to another register."))

        if register.user_id and register.user_id.id != user.id and register.status == "active":
            raise UserError(_("Register already in use by %s.") % register.user_id.name)

        if register.user_id and register.user_id.id == user.id and register.status == "active":
            if session:
                register.sudo().session_id = session
                session.chebu_register_id = register
            register.sudo().last_login = fields.Datetime.now()
            return {"success": True, "register": register._serialize()}

        register.sudo().write(
            {"user_id": user.id, "status": "active", "last_login": fields.Datetime.now()}
        )
        if session:
            register.sudo().session_id = session
            session.chebu_register_id = register
        return {"success": True, "register": register._serialize()}

    @api.model
    def release_register(self, register_id, user_id=None):
        register = self.browse(int(register_id)).exists()
        if not register:
            raise UserError(_("Register not found."))

        if user_id and int(user_id) != self.env.user.id:
            raise AccessError(_("You can only close your own register."))
        if register.user_id and register.user_id != self.env.user and not self.env.user.has_group(
            "point_of_sale.group_pos_manager"
        ):
            raise UserError(_("You cannot close another user's register."))

        register.sudo().write(
            {
                "user_id": False,
                "session_id": False,
                "status": "available",
                "last_logout": fields.Datetime.now(),
            }
        )
        return {"success": True, "register": register._serialize()}

    def action_start_sale(self):
        self.ensure_one()
        if self.status == "locked":
            raise UserError(_("This register is locked and cannot start a sale."))
        if self.status == "active" and self.user_id != self.env.user:
            raise AccessError(_("This register is currently in use by another user."))

        pos_config = self.pos_config_id
        if not pos_config:
            pos_configs = self.env["pos.config"].search(
                [("company_id", "=", self.company_id.id)], limit=2
            )
            if len(pos_configs) == 1:
                pos_config = pos_configs
                assigned_register = self.search(
                    [
                        ("company_id", "=", self.company_id.id),
                        ("pos_config_id", "=", pos_config.id),
                        ("id", "!=", self.id),
                    ],
                    limit=1,
                )
                if assigned_register:
                    raise UserError(
                        _(
                            "The only POS configuration is already assigned to %s. "
                            "Ask a Point of Sale manager to assign a separate configuration "
                            "in Register Settings."
                        )
                        % assigned_register.name
                    )
                self.sudo().pos_config_id = pos_config
            elif pos_configs:
                raise UserError(
                    _(
                        "This company has multiple POS configurations. Ask a Point of Sale "
                        "manager to assign the correct one in Register Settings."
                    )
                )
            else:
                raise UserError(
                    _(
                        "No POS configuration is set up for this company. Create one in "
                        "Point of Sale settings before starting a sale."
                    )
                )

        return {
            "type": "ir.actions.act_url",
            "name": _("New Sale"),
            "url": "/pos/ui?config_id=%s&chebu_register_id=%s"
            % (pos_config.id, self.id),
            "target": "self",
        }

    def action_open_settings(self):
        self.ensure_one()
        if not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise AccessError(_("Only Point of Sale managers can edit register settings."))
        settings_view = self.env.ref("chebu_pos.view_chebu_pos_register_settings_form")
        return {
            "type": "ir.actions.act_window",
            "name": _("Register Settings"),
            "res_model": "chebu.pos.register",
            "view_mode": "form",
            "views": [(settings_view.id, "form")],
            "res_id": self.id,
            "target": "current",
        }

    def action_view_pos_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Register Transactions"),
            "res_model": "pos.order",
            "view_mode": "list,form",
            "domain": [("session_id.chebu_register_id", "=", self.id)],
            "context": {"create": False, "edit": False, "delete": False},
        }

    def action_view_pos_session(self):
        self.ensure_one()
        if not self.session_id:
            raise UserError(_("This register does not have an open POS session."))
        return {
            "type": "ir.actions.act_window",
            "name": _("POS Session"),
            "res_model": "pos.session",
            "view_mode": "form",
            "res_id": self.session_id.id,
        }
