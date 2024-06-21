# -*- encoding: utf-8 -*-
{
	'name': u'Cargar Parámetros IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_journal_sequence'],
	'version': '1.0',
	'description':"""
		Crea y configura los parametros principales, los impuestos, etiquetas de cuenta y diarios.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'sql_update_main_parameter.sql',
		'wizard/upload_chart_account_it.xml'
	],
	'installable': True
}
