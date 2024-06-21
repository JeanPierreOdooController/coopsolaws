# -*- encoding: utf-8 -*-
{
    'name': 'Ecommerce seleccionar y autocompletar direccion',
    'category': 'uncategorize',
    'author': 'ITGRUPO',
    'depends': ['base'],
    'depends': ['website_sale','l10n_latam_base','query_ruc_dni','account_fields_it',
                'portal','portal_select_address_js_it'],
    'version': '1.0',
    'description':"""
     Descripcion
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'views/template_website_address.xml',
        'views/templates.xml',
        'views/website_add_company_shop.xml',
        #'views/portal_templates.xml',
        #'views/res_country_states.xml'
        ],
    'installable': True
}