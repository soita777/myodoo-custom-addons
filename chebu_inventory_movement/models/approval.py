from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InventoryApprovalPolicy(models.Model):
    _name = "chebu.inventory.approval.policy"
    _description = "Inventory Approval Policy"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    operation_type = fields.Selection(
        [
            ("movement", "Stock Movement"),
            ("transfer", "Internal Transfer"),
            ("return", "Return"),
            ("adjustment", "Inventory Adjustment"),
        ],
        required=True,
        default="movement",
    )
    min_quantity = fields.Float(default=0.0)
    min_value = fields.Monetary(default=0.0)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    approver_group_id = fields.Many2one("res.groups", required=True)
    blocking = fields.Boolean(default=True)
    required_approvals = fields.Integer(default=1)

    @api.constrains("required_approvals")
    def _check_required_approvals(self):
        for policy in self:
            if policy.required_approvals < 1:
                raise UserError(_("At least one approval is required."))


class InventoryApproval(models.Model):
    _name = "chebu.inventory.approval"
    _description = "Inventory Approval"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "requested_at desc, id desc"

    name = fields.Char(required=True, copy=False, default="New", index=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    policy_id = fields.Many2one("chebu.inventory.approval.policy", required=True)
    operation_type = fields.Selection(related="policy_id.operation_type", store=True)
    requester_id = fields.Many2one(
        "res.users", required=True, default=lambda self: self.env.user, readonly=True
    )
    requested_at = fields.Datetime(default=fields.Datetime.now, readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    quantity_total = fields.Float()
    value_total = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    reason = fields.Text()
    rejection_reason = fields.Text()
    ledger_ids = fields.One2many("chebu.inventory.movement.ledger", "approval_id")
    decision_ids = fields.One2many("chebu.inventory.approval.decision", "approval_id")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "chebu.inventory.approval"
                ) or "APP/NEW"
        return super().create(vals_list)

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        for approval in self:
            if not approval.policy_id.approver_group_id in self.env.user.groups_id:
                raise UserError(_("You are not authorized to approve this request."))
            approval.decision_ids.create({
                "approval_id": approval.id,
                "user_id": self.env.user.id,
                "decision": "approved",
            })
            approval.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class InventoryApprovalDecision(models.Model):
    _name = "chebu.inventory.approval.decision"
    _description = "Inventory Approval Decision"
    _order = "decided_at desc"

    approval_id = fields.Many2one("chebu.inventory.approval", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    decision = fields.Selection([("approved", "Approved"), ("rejected", "Rejected")], required=True)
    decided_at = fields.Datetime(default=fields.Datetime.now, readonly=True)
    comment = fields.Text()
