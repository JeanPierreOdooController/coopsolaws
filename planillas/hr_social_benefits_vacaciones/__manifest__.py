# -*- coding: utf-8 -*-
{
    'name': "Hr Social Benefits Compute Vacation",
    'category': 'hr',
	'author': 'ITGRUPO-HR',
    'depends': ['hr_leave_it','hr_social_benefits','hr_vacations_it'],
    'version': '1.0',
    'description': """
    Agregar pestaña de vacaciones para que se pueda acceder a esta
    """,
    'auto_install': False,
	'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/parameter.xml',
        'views/vacaciones.xml',
    ],
    'installable': True,
	'license': 'LGPL-3',
}