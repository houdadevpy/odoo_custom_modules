# -*- coding: utf-8 -*-
{
    'name': "customer_invoice_management",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Factura",
    'website': "https://myfactura.pro/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account',],

    
    # always loaded
    'data': [
        'security/invoice_security.xml',
        'security/ir.model.access.csv',
        'security/menu_limit_access.xml',
        'views/invoice_view.xml',
        'wizard/wizard_customer_invoice_report_view.xml',
        'wizard/wizard_report_preview.xml',
        'report/report_customer_invoice.xml',
        'report/customer_invoice_report_template.xml',
        'report/report_customer_invoice_summary.xml',
        'report/customer_invoice_report_summary_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    # 'ir.actions.report': [
    #     ('account.report_invoice', 'customer_invoice_management.action_report_customer_invoice'),
    # ],
}
