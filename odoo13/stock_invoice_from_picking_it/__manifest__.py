# -*- encoding: utf-8 -*-
{
	'name': 'generar Facturas de venta desde los albaranes',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['stock','account_base_it'],
	'version': '1.0',
	'description':"""
	 Agregar un boton Crear Factura en el albaran creado desde mantenimiento que permita
	, una vez realizado el albaran , poder generar la factura en borrador, jalando el dato de los
	productos .Una vez publicada se queda enlazada el numero de la factura al albaran.
	""",
	'auto_install': False,
	'demo': [],
	'data': [
		'views/picking_view.xml'
		],
	'installable': True
}