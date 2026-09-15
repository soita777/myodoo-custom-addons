from odoo import fields, models


class InventoryMovementDashboard(models.TransientModel):
    _name = "chebu.inventory.movement.dashboard"
    _description = "Inventory Movement Operations Dashboard"

    last_refreshed = fields.Datetime(default=fields.Datetime.now, readonly=True)
    movement_count = fields.Integer(compute="_compute_metrics")
    inbound_count = fields.Integer(compute="_compute_metrics")
    outbound_count = fields.Integer(compute="_compute_metrics")
    delivery_count = fields.Integer(compute="_compute_metrics")
    active_delivery_count = fields.Integer(compute="_compute_metrics")
    approval_count = fields.Integer(compute="_compute_metrics")
    pending_approval_count = fields.Integer(compute="_compute_metrics")

    def _compute_metrics(self):
        Ledger = self.env["chebu.inventory.movement.ledger"]
        Delivery = self.env["chebu.delivery.plan"]
        Approval = self.env["chebu.inventory.approval"]
        company_domain = [("company_id", "in", self.env.companies.ids)]
        for dashboard in self:
            dashboard.movement_count = Ledger.search_count(company_domain)
            dashboard.inbound_count = Ledger.search_count(company_domain + [("quantity_signed", ">", 0)])
            dashboard.outbound_count = Ledger.search_count(company_domain + [("quantity_signed", "<", 0)])
            dashboard.delivery_count = Delivery.search_count(company_domain)
            dashboard.active_delivery_count = Delivery.search_count(
                company_domain + [("state", "in", ["assigned", "in_transit"])]
            )
            dashboard.approval_count = Approval.search_count(company_domain)
            dashboard.pending_approval_count = Approval.search_count(
                company_domain + [("state", "=", "submitted")]
            )

    def action_refresh(self):
        self.ensure_one()
        self.last_refreshed = fields.Datetime.now()
        return {
            "type": "ir.actions.act_window",
            "name": "Operations Dashboard",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def _open_action(self, xml_id, name, domain=None):
        action = self.env.ref(xml_id).read()[0]
        action["name"] = name
        if domain:
            action["domain"] = domain
        return action

    def action_open_ledger(self):
        return self._open_action("chebu_inventory_movement.action_movement_ledger", "Live Movement Ledger")

    def action_open_deliveries(self):
        return self._open_action("chebu_inventory_movement.action_delivery_plan", "Delivery Session")

    def action_open_active_deliveries(self):
        return self._open_action(
            "chebu_inventory_movement.action_delivery_plan",
            "Active Deliveries",
            [("state", "in", ["assigned", "in_transit"])],
        )

    def action_open_approvals(self):
        return self._open_action(
            "chebu_inventory_movement.action_inventory_approval",
            "Approval Queue",
            [("state", "=", "submitted")],
        )
