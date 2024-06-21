# -*- encoding: utf-8 -*-
{
	'name': 'Gastos Vinculados desde Factura',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','landed_cost_it'],
	'version': '1.0',
	'description':"""
	- Enviar lineas de asiento a Gastos Vinculados
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/account_move.xml'
		],
	'installable': True
}
