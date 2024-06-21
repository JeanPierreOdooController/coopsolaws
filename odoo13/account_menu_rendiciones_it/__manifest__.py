# -*- encoding: utf-8 -*-
{
	'name': 'Menu Rendiciones',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_statement_payment','import_invoice'],
	'version': '1.0',
	'description':"""
        MENU DE REPORTES PARA LOCALIZACION CONTABLE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'views/menu_views.xml'
    ],
	'installable': True
}
