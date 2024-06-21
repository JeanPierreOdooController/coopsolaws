# -*- encoding: utf-8 -*-
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import Warning, UserError

class StockPMove(models.Model):
	_inherit = 'hr.quincenales'


	def action_wizard(self):
		for i in self:
			return {
				'name': 'Importar Lineas Quincenales',
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'res_model': 'import.fortnight.line',
				'context': {'default_fortnight_id': i.id},
				'target': 'new',
			}
		