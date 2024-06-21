# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	partner_adjustment_id = fields.Many2one('res.partner',string='Partner Ajustes DC')