# -*- encoding: utf-8 -*-
{
    'name': 'Vincular Facturas con Ventas y Compras',
    'category': 'PERSONLIZADO',
    'author': 'ITGRUPO',
    'depends': ['sale_management','account_accountant','show_field_invoices_purchase_js_it'],
    'version': '1.0',
    'description':"""
     Vincular Facturas con Compras
     LINK VIDEO: https://www.youtube.com/watch?v=oONCaGbuiqw
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        #'security/security.xml',
        'views.xml',
        ],
    'installable': True
}