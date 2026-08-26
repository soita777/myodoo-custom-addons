from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CompanyDevice(models.Model):
    _name = "company.device"
    _description = "Company Device"
    _order = "name"

    name = fields.Char(string="Device Name", required=True)
    serial_number = fields.Char(string="Serial Number", index=True)
    asset_tag = fields.Char(string="Asset Tag")
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
    )
    assigned_user = fields.Many2one("res.users", string="Assigned User")
    assigned_employee = fields.Many2one("hr.employee", string="Assigned Employee")
    assigned_by_id = fields.Many2one("res.users", string="Assigned By", readonly=True, copy=False)
    assigned_on = fields.Date(string="Assigned On", readonly=True, copy=False)
    assignment_ids = fields.One2many(
        "company.device.assignment", "device_id", string="Assignment History"
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
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_serial", "UNIQUE(serial_number)", "Serial number must be unique."),
    ]

    @api.onchange("assigned_employee")
    def _onchange_assigned_employee(self):
        if self.assigned_employee.user_id:
            self.assigned_user = self.assigned_employee.user_id

    @api.model_create_multi
    def create(self, vals_list):
        devices = super().create(vals_list)
        for device in devices:
            if device.assigned_employee:
                device._assign_to_employee(device.assigned_employee)
        return devices

    def write(self, vals):
        employee_changed = "assigned_employee" in vals
        result = super().write(vals)
        if employee_changed:
            for device in self:
                device._close_current_assignment()
                if device.assigned_employee:
                    device._assign_to_employee(device.assigned_employee)
                else:
                    device.write({"assigned_user": False, "assigned_by_id": False, "assigned_on": False})
        return result

    def _close_current_assignment(self):
        self.ensure_one()
        self.assignment_ids.filtered(lambda assignment: assignment.state == "assigned").write({
            "state": "returned", "returned_on": fields.Date.today(),
        })

    def _assign_to_employee(self, employee):
        self.ensure_one()
        assigned_on = fields.Date.today()
        self.with_context(skip_assignment_tracking=True).write({
            "assigned_user": employee.user_id.id,
            "assigned_by_id": self.env.user.id,
            "assigned_on": assigned_on,
        })
        self.env["company.device.assignment"].create({
            "device_id": self.id,
            "employee_id": employee.id,
            "assigned_by_id": self.env.user.id,
            "assigned_on": assigned_on,
        })


class CompanyDeviceAssignment(models.Model):
    _name = "company.device.assignment"
    _description = "Company Device Assignment"
    _order = "assigned_on desc, id desc"

    device_id = fields.Many2one("company.device", string="Device", required=True, ondelete="cascade")
    asset_tag = fields.Char(related="device_id.asset_tag", string="Asset Number", store=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    assigned_by_id = fields.Many2one("res.users", string="Assigned By", required=True, default=lambda self: self.env.user)
    assigned_on = fields.Date(string="Assigned On", required=True, default=fields.Date.today)
    state = fields.Selection([("assigned", "Assigned"), ("returned", "Returned")], default="assigned", required=True)
    returned_on = fields.Date(string="Returned On")

    @api.constrains("device_id", "state")
    def _check_one_active_assignment(self):
        for assignment in self.filtered(lambda record: record.state == "assigned"):
            if self.search_count([
                ("device_id", "=", assignment.device_id.id),
                ("state", "=", "assigned"),
                ("id", "!=", assignment.id),
            ]):
                raise ValidationError("A device can only have one active assignment.")
