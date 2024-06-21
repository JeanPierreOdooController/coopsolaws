# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResBank(models.Model):
    _inherit = 'res.bank'

    format_bank = fields.Selection([
    	('bbva', 'Formato BBVA'),
    	('bcp', 'Formato BCP'),
    	('interbank', 'Formato Interbank'),
    	('scotiabank', 'Formato Scotiabank'),
    	], string='Formato de Txt')