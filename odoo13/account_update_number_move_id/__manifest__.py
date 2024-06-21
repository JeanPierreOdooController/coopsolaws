# -*- encoding: utf-8 -*-
{
	'name': 'Actualizar Nombre con ID',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','import_journal_entry_it'],
	'version': '1.0',
	'description':"""
	- Actualizar Voucher con ID Asiento Contable
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'wizards/update_move_it_wizard.xml',
	],
	'installable': True
}