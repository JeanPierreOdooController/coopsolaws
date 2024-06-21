# -*- encoding: utf-8 -*-
{
	'name': 'Hr Account Move Consolidado IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it','hr_resumen_planilla_it', 'report_tools', 'popup_it'],
	'version': '1.0',
	'description':"""
	Modulo para generar Asiento Contable de la Planilla Central
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/hr_main_parameter.xml',
			'views/hr_resumen_planilla.xml',
			'views/hr_payslip_run_move.xml',
			'wizard/hr_payslip_run_move_wizard.xml',
			'hr_functions.sql'],
	'installable': True,
	'license': 'LGPL-3',
}