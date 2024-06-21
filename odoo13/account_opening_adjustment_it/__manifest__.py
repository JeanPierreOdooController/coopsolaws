# -*- encoding: utf-8 -*-
{
	'name': 'Ajuste de Apertura Contable It',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','l10n_pe_currency_rate'],
	'version': '1.0',
	'description':"""
	Sub-menu para creacion de Asiento de Ajuste de Aperturas Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'SQL.sql',
		'wizards/account_opening_adjustment_wizard.xml'
		],
	'installable': True
}
