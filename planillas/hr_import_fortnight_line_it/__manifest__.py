# -*- encoding: utf-8 -*-
{
	'name': 'Importador lineas Quincenales',
	'version': '1.0',
	'description': 'Importa datos reglas e inputs de las lineas quincenales',
	'author': 'ITGRUPO-HR',
	'license': 'LGPL-3',
	'category': 'HR',
	'depends': [
		'hr_fortnightly'
	],
	'data': [
        'security/ir.model.access.csv',
        'data/attachment_sample.xml',
		'views/hr_quincenales.xml',
        'wizard/import_fortnight_line.xml',
	],
	
	'auto_install': False,
	'application': False,
	
}