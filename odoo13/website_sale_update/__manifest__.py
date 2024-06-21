# -*- encoding: utf-8 -*-
{
	'name': 'Venta Electronica',
	'category': 'website',
	'author': 'ITGRUPO',
	'depends': ['website_sale','website_sale_delivery','website_sale_product_configurator','l10n_latam_base','account_base_it'],
	'version': '1.0',
	'description':"""
	Guias de Remision 
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/controller.xml'
	],
	'installable': True
}