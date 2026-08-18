{
    'name': 'Chebu M-Pesa Payments',
    'version': '18.0.1.0',
    'summary': 'Simple M-Pesa payment tracking app',
    'author': 'Chebu',
    'category': 'Accounting',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/mpesa_payment_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
