# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE Balances e Inventarios',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_sunat_rep_it','om_account_asset'],
	'version': '1.0',
	'description':"""
		- PLEs Balances e Inventarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'SQL.sql',
		'views/sunat_table_data.xml',
		'wizards/popup_it_balance_inventory.xml',
		'wizards/account_sunat_balance_inventory_rep.xml'
	],
	'installable': True
}