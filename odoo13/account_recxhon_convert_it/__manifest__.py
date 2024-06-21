# -*- encoding: utf-8 -*-
{
	'name': 'Convertir TXT a Excel Rec x Hon',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','import_journal_entry_it','import_invoice'],
	'version': '1.0',
	'description':"""
	Convertir TXT a Excel Rec x Hon
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizards/convert_recxhon_wizard.xml'
	],
	'installable': True
}