# -*- encoding: utf-8 -*-
{
    'name': 'Colocar Lotes en facturas',
    'category': 'uncategorize',
    'author': 'ITGRUPO',
    'depends': ['stock','popup_it','product_expiry','ebill'],
    'version': '1.0',
    'description':"""
     Importador de Lotes OML
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        #'security/security.xml',
        'views/stock_picking.xml',
        'views/account_move.xml'

        ],
    'installable': True
}