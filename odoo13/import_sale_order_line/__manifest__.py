# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Import Sale Order Lines from CSV/Excel file",
    "author" : "Softhealer Technologies-ITGRUPO",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",    
    "category": "Sales",
    "summary": "Import Sale Order Lines from CSV,Import Sale Order Lines from Excel, Import RFQ Lines From CSV Module, Import RFQ Lines From Excel App, Import PO Lines From CSV, import PO Lines From XLS, import request for quotation line XLSX Odoo",
    "description": """This module is useful to import Sale Order Lines from CSV/Excel. You can import custom fields from CSV or Excel.""", 
    "version":"13.0.2",
    "depends" : ["base", "popup_it", "sale"],
    "application" : True,
    "data" : [
            'data/attachment_sample.xml',
            'security/import_sol_security.xml',
            'wizard/import_sol_wizard.xml',
            'views/sale_view.xml',
            ],
    'external_dependencies' : {
        'python' : ['xlrd'],
    },
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/skJ5O8yV3gY",
    "auto_install":False,
    "installable" : True,
    "price": 15,
    "currency": "EUR"   
}
