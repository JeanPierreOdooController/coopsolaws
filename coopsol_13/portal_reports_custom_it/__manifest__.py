{
    'name': 'Portal Reports Custom',
    'version': '1.0',
    'description': 'Portal Reports Custom',
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'Portal, Dave',
    'auto_install': False,
    'depends': [
        'sale',
	'report_coopsol'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/button.xml',
    ],
    'installable': True
}