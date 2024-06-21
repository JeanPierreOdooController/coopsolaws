# -*- encoding: utf-8 -*-
{
	'name': 'Fields Coopsol',
	'category': 'Fields',
	'author': 'ITGRUPO-COOPSOL',
	'depends': ['base','sale','purchase'],
	'version': '1.0',
	'description':"""
	- Agregar campos para Coopsol
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/product_product.xml',
		'views/purchase_order.xml',
		'views/res_company.xml',
		'views/main_parameter_sale.xml',
		'views/res_partner.xml',
		'views/sale_order.xml',
		'views/res_partner_bank.xml'
	],
	'installable': True
}