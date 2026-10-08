from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.osv.expression import OR


class TemperatureGuruDevice(models.Model):
    _name = "temperature.guru.device"
    _description = "Temperature Monitoring Device"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "branch_id, name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, copy=False, readonly=True, default=lambda self: _("New"))
    serial_number = fields.Char(copy=False, index=True, tracking=True)
    device_type = fields.Selection(
        [
            ("refrigerator", "Refrigerator"),
            ("vaccine_fridge", "Vaccine Refrigerator"),
            ("freezer", "Freezer"),
            ("cold_room", "Cold Room"),
            ("other", "Other"),
        ],
        required=True,
        default="refrigerator",
        tracking=True,
    )
    branch_id = fields.Many2one(
        "chebu.inventory.branch", required=True, index=True, ondelete="restrict", tracking=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    location = fields.Char(required=True, tracking=True)
    minimum_temperature = fields.Float(default=2.0, required=True, tracking=True, digits=(6, 2))
    maximum_temperature = fields.Float(default=8.0, required=True, tracking=True, digits=(6, 2))
    stale_after_hours = fields.Integer(default=4, required=True)
    is_maintenance = fields.Boolean(default=False, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    note = fields.Text()
    reading_ids = fields.One2many("temperature.guru.reading", "device_id", string="Readings")
    current_temperature = fields.Float(compute="_compute_current_status", digits=(6, 2))
    last_reading_at = fields.Datetime(compute="_compute_current_status")
    current_status = fields.Selection(
        [
            ("normal", "Normal"),
            ("low", "Too Cold"),
            ("high", "Too Warm"),
            ("offline", "No Recent Reading"),
            ("no_data", "Awaiting First Reading"),
            ("maintenance", "In Maintenance"),
            ("inactive", "Inactive"),
        ],
        compute="_compute_current_status",
    )
    reading_count = fields.Integer(compute="_compute_reading_count")

    _sql_constraints = [
        ("temperature_guru_code_unique", "unique(code)", "Device code must be unique."),
        (
            "temperature_guru_serial_company_unique",
            "unique(company_id, serial_number)",
            "A device with this serial number already exists for this company.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", _("New")) == _("New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("temperature.guru.device") or _(
                    "New"
                )
        return super().create(vals_list)

    @api.constrains("branch_id", "company_id")
    def _check_branch_company(self):
        for device in self:
            if device.branch_id.company_id != device.company_id:
                raise ValidationError(_("The selected branch must belong to the device company."))

    @api.constrains("minimum_temperature", "maximum_temperature", "stale_after_hours")
    def _check_temperature_limits(self):
        for device in self:
            if device.minimum_temperature >= device.maximum_temperature:
                raise ValidationError(_("Maximum temperature must be above minimum temperature."))
            if device.stale_after_hours < 1:
                raise ValidationError(_("The stale-reading limit must be at least one hour."))

    @api.depends(
        "reading_ids.measured_at",
        "reading_ids.temperature_c",
        "minimum_temperature",
        "maximum_temperature",
        "stale_after_hours",
        "is_maintenance",
        "active",
    )
    def _compute_current_status(self):
        latest_by_device = {}
        if self.ids:
            groups = self.env["temperature.guru.reading"].read_group(
                [("device_id", "in", self.ids)], ["measured_at:max"], ["device_id"], lazy=False
            )
            latest_domains = [
                [("device_id", "=", group["device_id"][0]), ("measured_at", "=", group["measured_at"])]
                for group in groups
                if group.get("device_id") and group.get("measured_at")
            ]
            readings = (
                self.env["temperature.guru.reading"].search(OR(latest_domains), order="id desc")
                if latest_domains
                else self.env["temperature.guru.reading"]
            )
            for reading in readings:
                latest_by_device.setdefault(reading.device_id.id, reading)

        now = fields.Datetime.now()
        for device in self:
            reading = latest_by_device.get(device.id)
            device.current_temperature = reading.temperature_c if reading else 0.0
            device.last_reading_at = reading.measured_at if reading else False
            if not device.active:
                device.current_status = "inactive"
            elif device.is_maintenance:
                device.current_status = "maintenance"
            elif not reading:
                device.current_status = "no_data"
            elif reading.measured_at < now - timedelta(hours=device.stale_after_hours):
                device.current_status = "offline"
            elif reading.temperature_c < device.minimum_temperature:
                device.current_status = "low"
            elif reading.temperature_c > device.maximum_temperature:
                device.current_status = "high"
            else:
                device.current_status = "normal"

    @api.depends("reading_ids")
    def _compute_reading_count(self):
        counts = self.env["temperature.guru.reading"].read_group(
            [("device_id", "in", self.ids)], ["device_id"], ["device_id"], lazy=False
        ) if self.ids else []
        count_by_device = {
            group["device_id"][0]: group.get("device_id_count", 0)
            for group in counts
            if group.get("device_id")
        }
        for device in self:
            device.reading_count = count_by_device.get(device.id, 0)

    def action_view_readings(self):
        self.ensure_one()
        action = self.env.ref("temperature_guru.action_temperature_guru_readings").read()[0]
        action["domain"] = [("device_id", "=", self.id)]
        action["context"] = {"default_device_id": self.id, "default_branch_id": self.branch_id.id}
        return action


class TemperatureGuruReading(models.Model):
    _name = "temperature.guru.reading"
    _description = "Temperature Reading"
    _order = "measured_at desc, id desc"

    device_id = fields.Many2one(
        "temperature.guru.device", required=True, index=True, ondelete="restrict"
    )
    branch_id = fields.Many2one(
        related="device_id.branch_id", store=True, readonly=True, index=True
    )
    company_id = fields.Many2one(
        related="device_id.company_id", store=True, readonly=True, index=True
    )
    measured_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    temperature_c = fields.Float(required=True, digits=(6, 2), string="Temperature (°C)")
    status = fields.Selection(
        [("normal", "Normal"), ("low", "Too Cold"), ("high", "Too Warm")],
        compute="_compute_status",
        store=True,
    )
    note = fields.Char()

    @api.depends("temperature_c", "device_id.minimum_temperature", "device_id.maximum_temperature")
    def _compute_status(self):
        for reading in self:
            if reading.temperature_c < reading.device_id.minimum_temperature:
                reading.status = "low"
            elif reading.temperature_c > reading.device_id.maximum_temperature:
                reading.status = "high"
            else:
                reading.status = "normal"

    @api.constrains("temperature_c")
    def _check_temperature_range(self):
        for reading in self:
            if not -100 <= reading.temperature_c <= 100:
                raise ValidationError(_("Temperature must be between -100 °C and 100 °C."))

    @api.constrains("device_id", "company_id")
    def _check_reading_company(self):
        for reading in self:
            if reading.device_id.company_id not in self.env.companies:
                raise AccessError(_("You cannot log readings for another company."))


class TemperatureGuruDashboard(models.AbstractModel):
    _name = "temperature.guru.dashboard"
    _description = "Temperature Guru Dashboard Service"

    @api.model
    def get_dashboard_data(self, branch_id=None):
        companies = self.env.companies
        branches = self.env["chebu.inventory.branch"].search(
            [("company_id", "in", companies.ids), ("active", "=", True)], order="name"
        )
        if branch_id:
            branch = branches.filtered(lambda item: item.id == int(branch_id))
            if not branch:
                raise AccessError(_("The selected branch is not available to your user."))
            branches = branch

        branch_ids = branches.ids
        device_domain = [
            ("company_id", "in", companies.ids),
            ("branch_id", "in", branch_ids),
            ("active", "=", True),
        ]
        devices = self.env["temperature.guru.device"].search(device_domain, order="branch_id, name")
        device_rows = devices.read(
            [
                "id",
                "name",
                "code",
                "device_type",
                "branch_id",
                "location",
                "minimum_temperature",
                "maximum_temperature",
                "current_temperature",
                "last_reading_at",
                "current_status",
            ]
        )

        now = fields.Datetime.now()
        day_start = now - timedelta(hours=24)
        reading_domain = [
            ("company_id", "in", companies.ids),
            ("branch_id", "in", branch_ids),
            ("measured_at", ">=", day_start),
        ]
        Reading = self.env["temperature.guru.reading"]
        recent = Reading.search(reading_domain, order="measured_at desc, id desc", limit=200)
        reading_rows = [
            {
                "id": item.id,
                "device_id": item.device_id.id,
                "device_name": item.device_id.name,
                "device_code": item.device_id.code,
                "branch_id": item.branch_id.id,
                "branch_name": item.branch_id.name,
                "measured_at": fields.Datetime.to_string(item.measured_at),
                "temperature_c": item.temperature_c,
                "status": item.status,
                "note": item.note or "",
            }
            for item in recent[:12]
        ]

        chart_values = {}
        for item in reversed(recent):
            values = chart_values.setdefault(item.device_id.id, [])
            if len(values) < 12:
                values.append(item.temperature_c)
        for row in device_rows:
            row["branch_name"] = row["branch_id"][1] if row["branch_id"] else ""
            row["last_reading_at"] = (
                fields.Datetime.to_string(row["last_reading_at"]) if row["last_reading_at"] else False
            )
            row["chart_values"] = chart_values.get(row["id"], [])

        averages = Reading.read_group(
            reading_domain, ["temperature_c:avg", "id:count"], ["branch_id"], lazy=False
        ) if branch_ids else []
        average_by_branch = {
            group["branch_id"][0]: {
                "average": group.get("temperature_c", 0.0),
                "reading_count": group.get("id_count", 0),
            }
            for group in averages
            if group.get("branch_id")
        }
        branch_rows = [
            {
                "id": branch.id,
                "name": branch.name,
                "average": average_by_branch.get(branch.id, {}).get("average"),
                "reading_count": average_by_branch.get(branch.id, {}).get("reading_count", 0),
            }
            for branch in branches
        ]

        statuses = [row["current_status"] for row in device_rows]
        current_values = [
            row["current_temperature"] for row in device_rows if row["current_status"] in ("normal", "low", "high")
        ]
        return {
            "branches": branch_rows,
            "devices": device_rows,
            "recent_readings": reading_rows,
            "summary": {
                "device_count": len(device_rows),
                "normal_count": statuses.count("normal"),
                "attention_count": sum(status in ("low", "high", "offline") for status in statuses),
                "no_data_count": statuses.count("no_data"),
                "reading_count": Reading.search_count(reading_domain),
                "average_temperature": sum(current_values) / len(current_values) if current_values else False,
            },
            "selected_branch_id": int(branch_id) if branch_id else False,
        }