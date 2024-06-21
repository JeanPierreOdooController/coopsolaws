# -*- encoding: utf-8 -*-
{
	'name': 'Import Price Stock Line RQ IT',
	'version': '1.0',
	'description': '',
	'summary': '',
	'author': 'ITGRUPO',
	'website': '',
	'license': 'LGPL-3',
	'category': 'stock',
	'depends': [
		'stock'
	],
	'data': [
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
        'wizard/import_stock_price_line.xml',
        'views/stock_move.xml',
        'views/stock_picking.xml',
	],
	'demo': [
		''
	],
	'auto_install': False,
	'application': False,
	'assets': {

	}
}