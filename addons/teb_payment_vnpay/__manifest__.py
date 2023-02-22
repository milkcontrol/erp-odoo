# -*- coding: utf-8 -*-
{
    'name': "TeaBud VNPay Payment Providers",

    'summary': """Payment Acquirer:TeaBud VNPAy Implementation""",

    'description': """Payment Acquirer:TeaBud VNPAy Implementation""",

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['payment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_provider_views.xml',
        'views/payment_transaction_views.xml',
        'views/payment_vnpay_templates.xml',

        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'post_init_hook': 'post_init_hook',
    # 'post_init_hook': 'create_missing_journal_for_acquirers'
    'sequence': 30,
}