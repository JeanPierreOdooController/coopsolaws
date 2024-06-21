# -*- encoding: utf-8 -*-
{
	'name': 'Analisis de Consumo Detalle',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['kardex_account_journal_entry'],
	'version': '1.0',
	'description':"""
	- Reporte de Analisis de Consumo Detalle
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'security/security.xml',
		'wizards/consumption_analysis_wizard_detail.xml',
		'wizards/costs_sales_analysis_wizard_detail.xml',
		'views/consumption_analysis_book_detail.xml',
		'views/costs_sales_analysis_book_detail.xml'
	],
	'installable': True
}
