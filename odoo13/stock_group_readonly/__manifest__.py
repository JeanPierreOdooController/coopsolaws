# -*- coding: utf-8 -*-
{
    'name': "Bloquear campos de Informe de Inventario",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'stock',
    'description': """Bloquear los campos de editar de la vista tree del informe de inventario""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para stock',
    'depends': ['stock'],
    'data': [
        'views/grupo_readonly.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}