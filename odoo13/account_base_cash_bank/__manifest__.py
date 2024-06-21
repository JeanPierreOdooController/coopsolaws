# -*- encoding: utf-8 -*-
{
	'name': 'Reporte MOVIMIENTOS CAJA Y BANCO',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para MOVIMIENTOS CAJA Y BANCO
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'SQL.sql',
		'wizards/account_base_cash_bank_wizard.xml'
	],
	'installable': True
}
