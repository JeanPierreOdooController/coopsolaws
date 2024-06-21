# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	cci = fields.Char(string='CCI')
	is_account_detraction = fields.Boolean(string=u'Es Cuenta de Detracción',default=False)