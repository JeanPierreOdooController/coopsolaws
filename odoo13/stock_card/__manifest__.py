# -*- coding: utf-8 -*-
{
    'name': "Stock Card - Excel",

    'summary': """
        Habilita opcion de Kardex por producto en reportes de inventario
        """,

    'description': """
        Obten reporte de ingresos, salidas y saldos de stock por producto y ubicación. 
    """,

    'author': "David Lizarraga - Tecniases",
    'website': "https://www.tecniases.com",
    'category': 'Warehouse',
    'version': '0.1',

    # any module necessary for this one to work correctly

    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/stock_card_report.xml',
        'wizard/stock_card_wizard.xml',
    ],
}