import json

from odoo import http
from odoo.http import request


class MpesaCallback(http.Controller):
    @http.route('/mpesa/callback', type='http', auth='public', methods=['POST'], csrf=False)
    def mpesa_callback(self, **post):
        payload = json.dumps(post)
        transaction_id = post.get('TransactionId') or post.get('transactionId')
        payment = False
        if transaction_id:
            payment = request.env['chebu.mpesa.payment'].sudo().search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
        if payment:
            payment.sudo().write({
                'callback_payload': payload,
                'status': 'success' if str(post.get('ResultCode', '1')) == '0' else 'failed',
                'response_message': post.get('ResultDesc', 'Callback received'),
            })
        return request.make_response('OK', headers={'Content-Type': 'text/plain'})
