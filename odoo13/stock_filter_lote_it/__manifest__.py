{
    'name': 'Stock Filter Lote It',
    'version': '1.0',
    'description': 'Filtro de lotes en albaran segun almacenes',
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'stock picking',
    'auto_install': False,
    'depends': [ 'stock', 'stock_production_lot_validator' ],
    'data': [
        'views/move.xml',
        'views/move_line.xml',
    ],
    'installable': True
}