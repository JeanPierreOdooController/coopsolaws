# -*- encoding: utf-8 -*-
{
    'name': 'Hr Report Employee',
    'category': 'hr',
    'author': 'ITGRUPO-HR',
    'depends': ['hr_fields_it', 'report_tools', 'popup_it'],
    'version': '1.0',
    'description':"""
	    Modulo para generar varios reportes de planillas rrhh
	""",
    'auto_install': False,
    'demo': [],
    'data': [
        # 'security/ir.model.access.csv',
        'wizards/report_ficha_trabajador.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
