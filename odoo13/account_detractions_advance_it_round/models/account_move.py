# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.onchange('detraction_percent_id','amount_total')
	def onchange_detraction_percent_id(self):
		for move in self:
			if move.detraction_percent_id:
				move.code_operation = move.detraction_percent_id.code
				move.detra_amount = round(move.amount_total * move.detraction_percent_id.percentage)
			else:
				move.detra_amount = 0
				move.code_operation = None