# -*- encoding: utf-8 -*-
{
	'name': 'Destinos en Rango de Periodos',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_destinos_rep_it'],
	'version': '1.0',
	'description':"""
	Generar Destinos en Rango de Fechas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_des_detail_book.xml',
		'wizards/account_des_detail_range_rep.xml',
		'SQL.sql'
	],
	'installable': True
}
