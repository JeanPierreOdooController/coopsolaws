# -*- encoding: utf-8 -*-
{
	'name': 'Hr Resumen Planillas IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'report_tools', 'popup_it'],
	'version': '1.0',
	'description':"""
	Modulo para Consolidar y generar Planilla central del mes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'wizard/hr_planilla_tabular_wizard.xml',
			'views/hr_resumen_planilla.xml',
			'views/hr_resumen_planilla_line.xml',
			'views/hr_planilla_tabular.xml',
			],
	'installable': True,
	'license': 'LGPL-3',
}