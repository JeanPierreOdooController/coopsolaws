# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Saldos GV',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['landed_cost_it','kardex_valorado_it'],
	'version': '1.0',
	'description':"""
	- Reporte de Saldos en Gastos Vinculados
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/landed_cost_it_type.xml',
		'views/landed_cost_it.xml'
	],
	'installable': True
}