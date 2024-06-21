# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountAccount(models.Model):
	_inherit = 'account.account'

	dif_cambio_type = fields.Selection([('global','Global'),('doc','Por Documento')],default='global',string='Tipo Diferencia de Cambio')