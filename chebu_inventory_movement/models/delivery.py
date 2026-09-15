from odoo import api, fields, models
from odoo.exceptions import UserError


class InventoryDeliveryPlan(models.Model):
    _name = "chebu.delivery.plan"
    _description = "Inventory Delivery Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc, id desc"

    name = fields.Char(required=True, copy=False, default="New", index=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    branch_id = fields.Many2one("chebu.inventory.branch", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    sale_order_id = fields.Many2one("sale.order", index=True)
    pos_order_id = fields.Many2one("pos.order", index=True)
    picking_ids = fields.Many2many("stock.picking", string="Pickings")
    warehouse_id = fields.Many2one("stock.warehouse")
    scheduled_date = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("assigned", "Assigned"),
            ("in_transit", "In Transit"),
            ("delivered", "Delivered"),
            ("partial", "Partially Delivered"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
        index=True,
    )
    vehicle_id = fields.Many2one("fleet.vehicle")
    driver_employee_id = fields.Many2one("hr.employee", string="Driver")
    delivery_person_ids = fields.Many2many("hr.employee", string="Delivery Personnel")
    route_name = fields.Char()
    address_snapshot = fields.Text(string="Delivery Address")
    notes = fields.Text()
    stop_ids = fields.One2many("chebu.delivery.stop", "delivery_id")
    proof_ids = fields.One2many("chebu.delivery.proof", "delivery_id")
    pod_count = fields.Integer(compute="_compute_pod_count")

    @api.depends("proof_ids")
    def _compute_pod_count(self):
        for plan in self:
            plan.pod_count = len(plan.proof_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "chebu.delivery.plan"
                ) or "DEL/NEW"
        return super().create(vals_list)

    def action_plan(self):
        self.write({"state": "planned"})

    def action_assign(self):
        for plan in self:
            if not plan.vehicle_id or not plan.driver_employee_id:
                raise UserError("Assign a vehicle and driver before dispatch.")
        self.write({"state": "assigned"})

    def action_dispatch(self):
        self.write({"state": "in_transit"})

    def action_deliver(self):
        self.write({"state": "delivered"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class InventoryDeliveryStop(models.Model):
    _name = "chebu.delivery.stop"
    _description = "Delivery Stop"
    _order = "sequence, id"

    delivery_id = fields.Many2one("chebu.delivery.plan", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    partner_id = fields.Many2one("res.partner", required=True)
    address_snapshot = fields.Text()
    state = fields.Selection(
        [("pending", "Pending"), ("delivered", "Delivered"), ("failed", "Failed")],
        default="pending",
    )
    planned_datetime = fields.Datetime()
    actual_datetime = fields.Datetime()
    failure_reason = fields.Text()


class InventoryDeliveryProof(models.Model):
    _name = "chebu.delivery.proof"
    _description = "Proof of Delivery"
    _order = "received_at desc"

    delivery_id = fields.Many2one("chebu.delivery.plan", required=True, ondelete="cascade")
    stop_id = fields.Many2one("chebu.delivery.stop", ondelete="set null")
    received_by = fields.Char(required=True)
    received_at = fields.Datetime(required=True, default=fields.Datetime.now)
    result = fields.Selection(
        [("accepted", "Accepted"), ("partial", "Partial"), ("refused", "Refused")],
        required=True,
        default="accepted",
    )
    signature_attachment_id = fields.Many2one("ir.attachment", string="Signature")
    photo_attachment_ids = fields.Many2many("ir.attachment", string="Photos")
    customer_comment = fields.Text()
    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))
