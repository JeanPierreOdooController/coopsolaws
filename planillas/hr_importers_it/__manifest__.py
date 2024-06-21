# -*- encoding: utf-8 -*-
{
	'name': 'Hr Importers IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it','hr_fifth_category'],
	'version': '1.0',
	'description':"""
	Módulo para importar datos de empleados y contratos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/hr_payslip.xml',
		'wizard/hr_import_wizard.xml',
		'wizard/hr_import_wd_wizard.xml',
		'views/hr_menus.xml',
			],
	'installable': True
}