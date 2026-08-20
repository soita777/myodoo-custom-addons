from odoo import fields, models


class CompanyDevice(models.Model):
    _name = "company.device"
    _description = "Company Device"
    _order = "asset_number, name"

    name = fields.Char(string="Device Name", required=True)
    asset_number = fields.Char(string="Asset Number", required=True, index=True)
    serial_number = fields.Char(string="Serial Number", index=True)
    device_type = fields.Selection(
        [
            ("laptop", "Laptop"),
            ("desktop", "Desktop"),
            ("phone", "Phone"),
            ("tablet", "Tablet"),
            ("other", "Other"),
        ],
        string="Device Type",
        default="laptop",
        required=True,
    )
    assigned_user = fields.Many2one("res.users", string="Assigned User")
    assigned_employee = fields.Many2one("hr.employee", string="Assigned Employee")
    status = fields.Selection(
        [
            ("available", "Available"),
            ("assigned", "Assigned"),
            ("repair", "In Repair"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="available",
        required=True,
    )
    remotely_managed = fields.Boolean(string="Remotely Managed", default=False)
    remote_management_details = fields.Text(string="Remote Management Details")
    tracking_method = fields.Selection(
        [
            ("none", "None"),
            ("imei", "IMEI"),
            ("asset_tag", "Asset Tag"),
            ("agent", "Agent"),
        ],
        string="Tracking Method",
        default="none",
    )
    location = fields.Char(string="Location")
    purchase_date = fields.Date(string="Purchase Date")
    warranty_expiry = fields.Date(string="Warranty Expiry")
    retirement_date = fields.Date(string="Retirement Date")
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_asset_number", "UNIQUE(asset_number)", "Asset number must be unique."),
        ("unique_serial", "UNIQUE(serial_number)", "Serial number must be unique."),
    ]
