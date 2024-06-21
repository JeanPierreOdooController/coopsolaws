# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	is_followup_it = fields.Boolean(string='Informes de seguimiento', default=False)