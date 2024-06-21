# -*- coding: utf-8 -*-
{
    'name': "HR Automate Multipayment",
    'category': 'hr',
	'author': 'ITGRUPO-HR',
    'depends': [
        'hr_fields_it',
        'hr_social_benefits',
        'report_tools',
    ],
    'version': '1.0',
    'description': """
        Este módulo amplía el módulo de pagos multiples para manejar pagos de empleados.
    """,
    'auto_install': False,
	'demo': [],
    'data': [
        'security/security.xml',
		'security/ir.model.access.csv',
        'data/hr_type_document.xml',
        'views/res_bank.xml',
        'views/res_partner_bank.xml',
        'views/hr_automate_multipayment.xml',
        'views/hr_main_parameter.xml',
        'views/hr_payslip_run.xml',
    ],
    'installable': True
}
