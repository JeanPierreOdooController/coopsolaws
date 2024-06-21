# -*- encoding: utf-8 -*-
{
	'name': 'Importar Detracciones IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	- Se crea el menú Actualizar Detracciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'wizard/import_doc_invoice_relac_wizard.xml'
		],
	'installable': True
}
