# -*- encoding: utf-8 -*-
{
	'name': 'Estructura de Costos',
	'category': 'account',
	'author': 'ITGRUPO-COOPSOL',
	'depends': ['sale','report_tools'],
	'version': '1.0',
	'description':"""
	- Estructura de Costos en Formulario de Ventas
	- Submenu Estructura de Costos
	- Permiso "Estructura de Costos"
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/cost_structure_it.xml',
		'views/sale_order.xml'
	],
	'installable': True
}