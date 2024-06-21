# -*- coding: utf-8 -*-
{
    'name': "Editar 404",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'website',
    'description': """Bloquear los campos de crear y editar campo empleado a un grupo de usuarios""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para product',
    'depends': ['website','http_routing'],
    'data': [
        'security/ir.model.access.csv',
        'views/404_view.xml',
        'views/404_error.xml',
        'views/agregar.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}