# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountDelivery(models.Model):
	_name = 'account.delivery'
	_description = 'Account Delivery'

	name = fields.Char(string='Nombre')