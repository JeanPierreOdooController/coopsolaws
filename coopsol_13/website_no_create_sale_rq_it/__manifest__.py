{
    'name': 'Website No Create Sale RQ IT',
    'version': '1.0',
    'description': """
        No permite crear cotizaciones desde el website con el usuario publico, y para crearlo antes el usuario publico debe logearse
    """,
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'account',
    'auto_install': False,
    'depends': [
        'website_sale',
    ],
    'data': [
        # 'views/views.xml'
    ],
    'installable': True
}