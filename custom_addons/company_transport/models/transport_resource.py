from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CompanyTransportResource(models.Model):
    _name = "company.transport.resource"
    _description = "Company Transport Resource"
    _order = "name"

    name = fields.Char(string="Resource Name", required=True)
    resource_type = fields.Selection(
        [
            ("car", "Car"),
            ("van", "Van"),
            ("truck", "Truck"),
            ("motorcycle", "Motorcycle"),
            ("trailer", "Trailer"),
            ("other", "Other"),
        ],
        string="Resource Type",
        required=True,
        default="car",
    )
    registration_number = fields.Char(string="Registration Number", index=True)
    vin = fields.Char(string="VIN / Chassis Number", index=True)
    make = fields.Char(string="Make")
    model = fields.Char(string="Model")
    year = fields.Integer(string="Year")
    color = fields.Char(string="Color")
    ownership = fields.Selection(
        [("owned", "Company Owned"), ("leased", "Leased"), ("rented", "Rented")],
        string="Ownership",
        default="owned",
        required=True,
    )
    state = fields.Selection(
        [
            ("available", "Available"),
            ("assigned", "Assigned"),
            ("maintenance", "Under Maintenance"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="available",
        required=True,
    )
    assigned_employee = fields.Many2one("hr.employee", string="Assigned Driver")
    assigned_user = fields.Many2one(
        "res.users", related="assigned_employee.user_id", string="User", store=True
    )
    location = fields.Char(string="Current Location")
    fuel_type = fields.Selection(
        [
            ("petrol", "Petrol"),
            ("diesel", "Diesel"),
            ("electric", "Electric"),
            ("hybrid", "Hybrid"),
            ("other", "Other"),
        ],
        string="Fuel Type",
    )
    odometer = fields.Float(string="Odometer (km)")
    registration_expiry = fields.Date(string="Registration Expiry")
    insurance_expiry = fields.Date(string="Insurance Expiry")
    inspection_expiry = fields.Date(string="Inspection Expiry")
    last_service_date = fields.Date(string="Last Service Date")
    next_service_date = fields.Date(string="Next Service Date")
    purchase_date = fields.Date(string="Purchase / Lease Date")
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_registration_number",
            "UNIQUE(registration_number)",
            "Registration number must be unique.",
        ),
        ("unique_vin", "UNIQUE(vin)", "VIN / chassis number must be unique."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("assigned_employee") and "state" not in vals:
                vals["state"] = "assigned"
        return super().create(vals_list)

    def write(self, vals):
        if "assigned_employee" in vals and "state" not in vals:
            vals = dict(vals)
            vals["state"] = "assigned" if vals["assigned_employee"] else "available"
        return super().write(vals)

    @api.constrains("year")
    def _check_year(self):
        for resource in self:
            if resource.year and not 1900 <= resource.year <= fields.Date.today().year + 1:
                raise ValidationError("Year must be between 1900 and next year.")

    @api.constrains("odometer")
    def _check_odometer(self):
        for resource in self:
            if resource.odometer < 0:
                raise ValidationError("Odometer cannot be negative.")

    @api.onchange("assigned_employee")
    def _onchange_assigned_employee(self):
        for resource in self:
            if resource.assigned_employee and resource.state == "available":
                resource.state = "assigned"
            elif not resource.assigned_employee and resource.state == "assigned":
                resource.state = "available"

    @api.constrains("state", "assigned_employee")
    def _check_assignment(self):
        for resource in self:
            if resource.state == "assigned" and not resource.assigned_employee:
                raise ValidationError("An assigned resource must have an assigned driver.")
            if resource.state != "assigned" and resource.assigned_employee:
                raise ValidationError("Only assigned resources can have an assigned driver.")
