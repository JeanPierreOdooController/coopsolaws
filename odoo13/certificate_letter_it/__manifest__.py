{
    'name': 'Certificados y Carta',
    'version': '1.0',
    'description': 'Exportación de certificados y Cartas en doc',
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'Empleado',
    'auto_install': False,
    'depends': [
        'hr'
    ],
    'data': [
        'security/security.xml',
        'report/certificate.xml',
        'report/letter.xml',
        'views/view.xml',
        'views/view_letter.xml',
    ],
    'installable': True
}
