# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPettyCash(models.Model):
	_name = 'account.petty.cash'
	_description = 'Account Petty Cash'

	name = fields.Char(string='Nombre')