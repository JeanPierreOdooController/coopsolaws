# -*- encoding: utf-8 -*-
{
	'name': 'Analisis de Ventas',
	'category': 'PERSONALIZADO',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','sale'],
	'version': '1.0',
	'description':"""
	Submenu para Analisis de Ventas en Ventas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/sale_analysis_book.xml',
		'views/sale_analysis_book_powerby.xml',
		'wizard/sale_analysis_wizard.xml',
        'wizard/sale_analysis_wizard_powerby.xml',
		],
	'installable': True
}