# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date

class UpdateTcMoveLineWizard(models.TransientModel):
	_name = 'update.tc.move.line.wizard'
	_description = 'Update Tc Move Line Wizard'

	period_id = fields.Many2one('account.period',string='Periodo')

	def update_lines(self):
		sql = """update account_move_line set tc = round(abs((debit-credit)/amount_currency),3) where (date between '%s' and '%s') and (tc is null or tc = 0 or tc = 1) and currency_id is not null and coalesce(amount_currency,0) <> 0""" % (self.period_id.date_start.strftime('%Y/%m/%d'),
			self.period_id.date_end.strftime('%Y/%m/%d'))
		self.env.cr.execute(sql)
		return self.env['popup.it'].get_message('Se termino de Regularizar los tc en las lineas contables en moneda extranjera.')