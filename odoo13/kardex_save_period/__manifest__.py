# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Save Period IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['kardex_valorado_it'],
	'version': '1.0',
	'description':"""
	- Kardex almacenado mensual
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/kardex.xml',
		],
	'installable': True
}