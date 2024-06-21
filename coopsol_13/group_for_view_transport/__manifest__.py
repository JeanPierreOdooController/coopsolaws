# -*- encoding: utf-8 -*-
{
	'name': 'Grupo para Editar Pestaña TRANSPORTISTA de Albarán',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['stock_picking_note'],
	'version': '1.0',
	'description':"""
	- Grupo especial para editar datos de la pestaña "TRANSPORTISTA" aun estando en estado Validado.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'views/stock_picking.xml'
	],
	'installable': True
}