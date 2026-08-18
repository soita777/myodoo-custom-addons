{
    'name': 'Chebu M-Pesa STK Push',
    'version': '18.0.1.0',
    'summary': 'M-Pesa STK Push payment handling for Odoo',
    'author': 'Chebu',
    'category': 'Accounting',
    'depends': ['base', 'mail', 'project'],
    'data': [
        'data/ir_sequence.xml',
        'security/mpesa_security.xml',
        'security/ir.model.access.csv',
        'views/mpesa_payment_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
