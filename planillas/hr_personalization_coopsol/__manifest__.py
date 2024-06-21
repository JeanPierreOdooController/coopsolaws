# -*- encoding: utf-8 -*-
{
	'name': 'Hr Personalizaciones Coopsol',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it','account_fields_it','hr_voucher_it','hr_importers_it'],
	'version': '1.0',
	'description':"""
	Módulo para importar datos de empleados y contratos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		# 'security/ir.model.access.csv',
		'views/res_partner.xml',
		'views/hr_contract.xml',
		'views/hr_payslip_worked_days_type.xml',
			],
	'installable': True,
	'license': 'LGPL-3',
}