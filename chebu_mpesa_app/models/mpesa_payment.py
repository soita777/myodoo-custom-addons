from odoo import api, fields, models, _


class ChebuMpesaPayment(models.Model):
    _name = 'chebu.mpesa.payment'
    _description = 'M-Pesa Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Payment Reference', required=True, copy=False, default='New', index=True)
    customer_reference = fields.Char(
        string='Customer Reference',
        copy=False,
        index=True,
        help='The customer, invoice, account, or order reference associated with this payment.',
    )
    partner_id = fields.Many2one('res.partner', string='Customer', index=True)
    mode_of_payment = fields.Selection([
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('other', 'Other'),
    ], string='Mode of Payment', default='mpesa', required=True, index=True)
    amount = fields.Float(string='Amount (KES)', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.ref('base.KES'))
    phone_number = fields.Char(string='Phone Number', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', index=True)
    transaction_id = fields.Char(string='Transaction ID', copy=False, index=True)
    response_message = fields.Text(string='Response Message')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('chebu.mpesa.payment') or 'MPESA'
        return super().create(vals_list)
