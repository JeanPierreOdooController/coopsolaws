# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPatrimonyType(models.Model):
	_name = 'account.patrimony.type'
	_description = 'Account Patrimony Type'

	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo')