from odoo import api, fields, models


class MyArenaNote(models.Model):
    _name = "my.arena.note"
    _description = "My Arena Note"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "is_pinned desc, write_date desc, id desc"

    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
        default="Untitled Note",
    )
    body = fields.Html(string="Note", sanitize=True)
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        required=True,
        default=lambda self: self.env.user,
        index=True,
        ondelete="cascade",
    )
    tag_ids = fields.Many2many(
        "my.arena.note.tag",
        "my_arena_note_tag_rel",
        "note_id",
        "tag_id",
        string="Tags",
    )
    color = fields.Integer(string="Color")
    is_pinned = fields.Boolean(string="Pinned", tracking=True)
    is_archived = fields.Boolean(string="Archived", tracking=True)
    priority = fields.Selection(
        [
            ("0", "Normal"),
            ("1", "Important"),
            ("2", "Urgent"),
        ],
        string="Priority",
        default="0",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("user_id", self.env.user.id)
        return super().create(vals_list)


class MyArenaNoteTag(models.Model):
    _name = "my.arena.note.tag"
    _description = "My Arena Note Tag"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(string="Color")
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        required=True,
        default=lambda self: self.env.user,
        index=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "name_user_uniq",
            "unique(name, user_id)",
            "You already have a tag with this name.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("user_id", self.env.user.id)
        return super().create(vals_list)
