import base64
import json
import time
import urllib.request
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class ChebuMpesaPayment(models.Model):
    _name = 'chebu.mpesa.payment'
    _description = 'M-Pesa STK Push Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    amount = fields.Float(string='Amount (KES)', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.ref('base.KES'))
    phone_number = fields.Char(string='Phone Number', required=True, tracking=True)
    transaction_id = fields.Char(string='Transaction ID', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True)
    response_code = fields.Char(string='Response Code')
    response_message = fields.Char(string='Response Message')
    callback_payload = fields.Text(string='Callback Payload')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    create_date = fields.Datetime(string='Created On', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('chebu.mpesa.payment') or 'MPESA'
        return super().create(vals_list)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    @api.constrains('phone_number')
    def _check_phone(self):
        for rec in self:
            if rec.phone_number and not rec.phone_number.isdigit():
                raise ValidationError(_('Phone number must contain digits only.'))
            if rec.phone_number and len(rec.phone_number) < 9:
                raise ValidationError(_('Phone number must be at least 9 digits.'))

    def _get_provider_config(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            'base_url': params.get_param('chebu.mpesa.base_url', 'https://sandbox.safaricom.co.ke'),
            'consumer_key': params.get_param('chebu.mpesa.consumer_key', ''),
            'consumer_secret': params.get_param('chebu.mpesa.consumer_secret', ''),
            'short_code': params.get_param('chebu.mpesa.short_code', ''),
            'passkey': params.get_param('chebu.mpesa.passkey', ''),
            'callback_url': params.get_param('chebu.mpesa.callback_url', ''),
        }

    def _get_access_token(self, config):
        if not config['consumer_key'] or not config['consumer_secret']:
            raise UserError(_('Set the M-Pesa consumer key and secret in Odoo settings first.'))
        auth = base64.b64encode(f"{config['consumer_key']}:{config['consumer_secret']}".encode('utf-8')).decode('utf-8')
        request = urllib.request.Request(
            f"{config['base_url']}/oauth/v1/generate?grant_type=client_credentials",
            headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'},
            method='GET',
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode('utf-8'))
            access_token = payload.get('access_token')
            if not access_token:
                raise UserError(_('M-Pesa token generation returned no access token.'))
            return access_token
        except Exception as exc:
            raise UserError(_('Unable to fetch M-Pesa access token: %s') % exc) from exc

    def _build_password(self, config, timestamp):
        if not config['short_code'] or not config['passkey']:
            raise UserError(_('Set the M-Pesa short code and passkey in Odoo settings first.'))
        raw = f"{config['short_code']}{config['passkey']}{timestamp}".encode('utf-8')
        return base64.b64encode(raw).decode('utf-8')

    def action_send_stk_push(self):
        self.ensure_one()
        if self.status == 'success':
            raise UserError(_('This payment is already marked as successful.'))

        config = self._get_provider_config()
        timestamp = time.strftime('%Y%m%d%H%M%S')
        access_token = self._get_access_token(config)
        password = self._build_password(config, timestamp)
        callback_url = config.get('callback_url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/mpesa/callback'

        payload = {
            'BusinessShortCode': config['short_code'],
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(self.amount),
            'PartyA': self.phone_number,
            'PartyB': config['short_code'],
            'PhoneNumber': self.phone_number,
            'CallBackURL': callback_url,
            'AccountReference': self.partner_id.name or self.name,
            'TransactionDesc': f'Payment {self.name}',
        }
        request_data = json.dumps(payload).encode('utf-8')
        stk_request = urllib.request.Request(
            f"{config['base_url']}/mpesa/stkpush/v1/processrequest",
            data=request_data,
            headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(stk_request, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
            self.write({
                'status': 'pending',
                'response_code': response_data.get('ResponseCode', 'pending'),
                'response_message': response_data.get('CustomerMessage', response_data.get('ResponseDescription', 'Request sent')),
                'transaction_id': response_data.get('CheckoutRequestID') or self.transaction_id,
            })
            return True
        except Exception as exc:
            self.write({
                'status': 'failed',
                'response_code': 'error',
                'response_message': str(exc),
            })
            raise UserError(_('STK Push request failed: %s') % exc) from exc
