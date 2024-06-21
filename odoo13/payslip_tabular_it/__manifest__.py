{
    'name': 'Tabular Planilla',
    'version': '1.0',
    'description': 'Crea vista pivot de la planilla por empleado',
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'hr_payroll',
    'auto_install': False,
    'depends': [
        'hr_payroll'
    ],
    'data': [
        'views/view_pivot.xml'
    ],
    'installable': True
}