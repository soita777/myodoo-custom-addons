from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InventoryMovementLedger(models.Model):
    _name = "chebu.inventory.movement.ledger"
    _description = "Inventory Movement Ledger"
    _order = "effective_datetime desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, default="New", index=True, readonly=True)
    company_id = fields.Many2one("res.company", required=True, index=True, readonly=True)
    branch_id = fields.Many2one("chebu.inventory.branch", index=True, readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", index=True, readonly=True)
    product_id = fields.Many2one("product.product", required=True, index=True, readonly=True)
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id", store=True, readonly=True)
    product_uom_id = fields.Many2one("uom.uom", required=True, readonly=True)
    quantity = fields.Float(required=True, readonly=True)
    quantity_signed = fields.Float(required=True, readonly=True)
    source_location_id = fields.Many2one("stock.location", required=True, index=True, readonly=True)
    destination_location_id = fields.Many2one("stock.location", required=True, index=True, readonly=True)
    lot_id = fields.Many2one("stock.lot", index=True, readonly=True)
    package_id = fields.Many2one("stock.quant.package", index=True, readonly=True)
    owner_id = fields.Many2one("res.partner", readonly=True)
    movement_type = fields.Selection(
        [
            ("purchase_receipt", "Purchase Receipt"),
            ("customer_delivery", "Customer Delivery"),
            ("internal_transfer", "Internal Transfer"),
            ("pos_sale", "Point of Sale Sale"),
            ("return_in", "Return In"),
            ("return_out", "Return Out"),
            ("inventory_adjustment_in", "Inventory Adjustment In"),
            ("inventory_adjustment_out", "Inventory Adjustment Out"),
            ("scrap", "Scrap"),
            ("other", "Other"),
        ],
        required=True,
        index=True,
        readonly=True,
    )
    stock_move_id = fields.Many2one("stock.move", index=True, readonly=True)
    stock_move_line_id = fields.Many2one("stock.move.line", index=True, readonly=True)
    picking_id = fields.Many2one("stock.picking", index=True, readonly=True)
    sale_order_id = fields.Many2one("sale.order", index=True, readonly=True)
    purchase_order_id = fields.Many2one("purchase.order", index=True, readonly=True)
    pos_order_id = fields.Many2one("pos.order", index=True, readonly=True)
    user_id = fields.Many2one("res.users", index=True, readonly=True)
    effective_datetime = fields.Datetime(required=True, index=True, readonly=True)
    recorded_datetime = fields.Datetime(default=fields.Datetime.now, readonly=True)
    approval_state = fields.Selection(
        [("not_required", "Not Required"), ("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="not_required",
        required=True,
        index=True,
        readonly=True,
    )
    approval_id = fields.Many2one("chebu.inventory.approval", index=True, readonly=True)
    value_company_currency = fields.Monetary(currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True, readonly=True)
    external_reference = fields.Char(index=True, copy=False, readonly=True)

    _sql_constraints = [
        (
            "source_move_line_unique",
            "UNIQUE(stock_move_line_id)",
            "A completed stock move line can only be captured once.",
        ),
        ("positive_quantity", "CHECK(quantity > 0)", "Ledger quantity must be positive."),
        ("nonzero_signed_quantity", "CHECK(quantity_signed != 0)", "Signed quantity cannot be zero."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "chebu.inventory.movement.ledger"
                ) or "MOV/NEW"
        return super().create(vals_list)

    @api.model
    def _movement_type_for_line(self, line):
        picking = line.picking_id
        if picking and picking.picking_type_id.code == "incoming":
            return "purchase_receipt"
        if picking and picking.picking_type_id.code == "outgoing":
            return "customer_delivery"
        if picking and picking.picking_type_id.code == "internal":
            return "internal_transfer"
        if line.location_id.usage == "inventory":
            return "inventory_adjustment_in"
        if line.location_dest_id.usage == "inventory":
            return "inventory_adjustment_out"
        if line.location_dest_id.usage == "customer":
            return "customer_delivery"
        return "other"

    @api.model
    def capture_completed_moves(self, limit=1000):
        lines = self.env["stock.move.line"].search(
            [("state", "=", "done"), ("quantity", "!=", 0)],
            order="id",
            limit=limit,
        )
        existing_ids = set(self.search([("stock_move_line_id", "in", lines.ids)]).mapped("stock_move_line_id").ids)
        vals_list = []
        for line in lines:
            if line.id in existing_ids:
                continue
            quantity = abs(line.quantity)
            movement_type = self._movement_type_for_line(line)
            incoming = line.location_dest_id.usage in ("internal", "transit")
            vals_list.append({
                "company_id": line.company_id.id,
                "product_id": line.product_id.id,
                "product_uom_id": line.product_uom_id.id,
                "quantity": quantity,
                "quantity_signed": quantity if incoming else -quantity,
                "source_location_id": line.location_id.id,
                "destination_location_id": line.location_dest_id.id,
                "lot_id": line.lot_id.id,
                "package_id": (line.result_package_id or line.package_id).id,
                "owner_id": line.owner_id.id,
                "movement_type": movement_type,
                "stock_move_id": line.move_id.id,
                "stock_move_line_id": line.id,
                "picking_id": line.picking_id.id,
                "sale_order_id": line.move_id.sale_line_id.order_id.id,
                "purchase_order_id": line.move_id.purchase_line_id.order_id.id,
                "user_id": self.env.user.id,
                "effective_datetime": line.date,
                "external_reference": "stock.move.line:%s" % line.id,
            })
        if vals_list:
            self.create(vals_list)
        return len(vals_list)

    @api.model
    def cron_capture_completed_moves(self):
        self.capture_completed_moves()

    def write(self, vals):
        if not self.env.user.has_group("chebu_inventory_movement.group_inventory_movement_admin"):
            protected = set(vals) & set(self._fields)
            protected -= {"message_follower_ids", "message_ids", "activity_ids"}
            if protected:
                raise UserError(_("Ledger facts are immutable."))
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group("chebu_inventory_movement.group_inventory_movement_admin"):
            raise UserError(_("Ledger facts cannot be deleted."))
        return super().unlink()
