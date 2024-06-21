# -*- encoding: utf-8 -*-
{
	'name': 'Report Coopsol',
	'category': 'Report',
	'author': 'ITGRUPO-COOPSOL',
	'depends': ['coopsol_fields_it','report_tools','product'],
	'version': '1.0',
	'description':"""
	- Reporte de Cotizacion por Producto en product.product
	- Reporte de Pedido de Venta
	- Report de Orden de Compra Local
	- Report de Orden de Compra Exterior
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/product_product.xml',
		'views/purchase_order.xml',
		#'views/sale_order.xml',
		'wizard/sale_for_product_wizard.xml',
		'wizard/purchase_order_print_wizard.xml',
		'report/report_sale.xml'
	],
	'installable': True
}