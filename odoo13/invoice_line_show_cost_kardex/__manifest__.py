# -*- encoding: utf-8 -*-
{
	'name': 'costo kardex en factura',
	'category': 'PERSONALIZADO',
	'author': 'ITGRUPO',
	'depends': ['account','kardex_valorado_it','kardex_fisico_it'],
	'version': '1.0',
	'description':"""
	costo kardex en factura
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move_line.xml'
		],
	'installable': True
}