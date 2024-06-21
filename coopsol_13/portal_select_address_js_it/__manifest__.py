# -*- encoding: utf-8 -*-
{
    'name': 'Portal seleccionar y autocompletar direccion',
    'category': 'uncategorize',
    'author': 'ITGRUPO',
    'depends': ['base'],
    'depends': ['l10n_latam_base','query_ruc_dni','account_fields_it','portal','contacts'],
    'version': '1.0',
    'description':"""
     Descripcion
    """,
    'auto_install': False,
    'demo': [],
    'data': [

        'views/templates.xml',

        'views/portal_templates.xml',
        'views/res_country_states.xml'
        ],
    'installable': True
}