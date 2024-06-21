# -*- coding: utf-8 -*-
{
    'name': "Product reserva report",
    'category': 'Website',
    'sequence': 5,
    'summary': """Atharva Theme General""",
    'version': '2.3',
    'author': 'Atharva System',
    'support': 'support@atharvasystem.com',
    'website' : 'http://www.atharvasystem.com',
    'license' : 'OPL-1',
    'description': """
        Base Module for all themes by Atharva System""",
    'depends': [
        'sale','purchase'
    ],
    'data': [
        'views/product_brand_views.xml',
    ],
    'installable': True,
    'application': True
}
