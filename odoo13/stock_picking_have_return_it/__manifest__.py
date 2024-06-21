# -*- coding: utf-8 -*-
{
    'name': "ALBARANES DEVUELTOS NO DEBEN APARECER EN LISTA DE DESPACHO LUBTEC (#9679)",

    'summary': """""",

    'description': """
       ALBARANES DEVUELTOS NO DEBEN APARECER EN LISTA DE DESPACHO LUBTEC (#9679)

    """,

    'author': "ITGRUPO",
    'category': 'stock',
    'version': '1.0',
    'depends': ['picking_distpatch_it'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking.xml',
    ],
    'demo': [],
}
