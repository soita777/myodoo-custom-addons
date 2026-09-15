from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InventoryTransferLauncher(models.TransientModel):
    _name = "chebu.inventory.transfer.launcher"
    _description = "Quick Internal Transfer Launcher"

    source_warehouse_id = fields.Many2one(
        "stock.warehouse", string="Stock leaving from", required=True,
        default=lambda self: self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], order="name", limit=1
        ),
    )
    source_location_id = fields.Many2one(
        "stock.location", related="source_warehouse_id.lot_stock_id", string="Source Location"
    )
    company_id = fields.Many2one("res.company", related="source_warehouse_id.company_id", store=True)
    destination_line_ids = fields.One2many(
        "chebu.inventory.transfer.destination", "launcher_id", string="Transfer Destinations"
    )

    @api.onchange("source_warehouse_id")
    def _onchange_source_warehouse_id(self):
        for launcher in self:
            warehouses = self.env["stock.warehouse"].search(
                [("company_id", "=", launcher.company_id.id or self.env.company.id),
                 ("id", "!=", launcher.source_warehouse_id.id)], order="name"
            )
            launcher.destination_line_ids = [
                fields.Command.create({"destination_warehouse_id": warehouse.id})
                for warehouse in warehouses
            ]

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        source_id = values.get("source_warehouse_id")
        if source_id and "destination_line_ids" in fields_list:
            warehouses = self.env["stock.warehouse"].search(
                [("company_id", "=", self.env.company.id), ("id", "!=", source_id)], order="name"
            )
            values["destination_line_ids"] = [
                fields.Command.create({"destination_warehouse_id": warehouse.id})
                for warehouse in warehouses
            ]
        return values


class InventoryTransferDestination(models.TransientModel):
    _name = "chebu.inventory.transfer.destination"
    _description = "Quick Transfer Destination"

    launcher_id = fields.Many2one("chebu.inventory.transfer.launcher", required=True, ondelete="cascade")
    destination_warehouse_id = fields.Many2one("stock.warehouse", required=True)
    source_warehouse_id = fields.Many2one(related="launcher_id.source_warehouse_id", string="Source Warehouse")
    source_location_id = fields.Many2one(related="launcher_id.source_location_id")
    destination_location_id = fields.Many2one(related="destination_warehouse_id.lot_stock_id", string="Destination Location")
    route_label = fields.Char(compute="_compute_route_label")

    @api.depends("source_warehouse_id", "destination_warehouse_id")
    def _compute_route_label(self):
        for line in self:
            line.route_label = _("%s to %s") % (
                line.source_location_id.display_name or _("Source"),
                line.destination_location_id.display_name or _("Destination"),
            )

    def action_start_transfer(self):
        self.ensure_one()
        if not self.source_location_id or not self.destination_location_id:
            raise UserError(_("Both warehouses must have an internal stock location."))
        picking_type = self.source_warehouse_id.int_type_id
        if not picking_type:
            raise UserError(_("The source warehouse has no internal transfer operation type."))
        picking = self.env["stock.picking"].create({
            "picking_type_id": picking_type.id,
            "location_id": self.source_location_id.id,
            "location_dest_id": self.destination_location_id.id,
            "origin": _("Quick Transfer: %s to %s") % (
                self.source_warehouse_id.name, self.destination_warehouse_id.name,
            ),
        })
        return picking.get_formview_action()