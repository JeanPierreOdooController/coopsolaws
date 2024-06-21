# -*- encoding: utf-8 -*-
{
	'name': 'Actualizar TC Apuntes Contables',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_consistencia_rep_it'],
	'version': '1.0',
	'description':"""
		- Actualizar TC en base a balance e importe en moneda
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizards/update_tc_move_line_wizard.xml'
	],
	'installable': True
}