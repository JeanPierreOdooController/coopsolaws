from odoo import models, fields, exceptions, api, _
from odoo.exceptions import Warning, UserError

class StockPMove(models.Model):
	_inherit = 'stock.move'
	
		
	def action_wizard(self):
		stock_move_ids = []    
		for move in self:
			if move.picking_id.picking_type_id.code == 'incoming':
				stock_move_ids.append(move.id)
			else:
				raise UserError("El Importador de Costos de Transferencia solo está disponible en los tipos de operación RECIBO")

		return {
			'name': 'Actualizador de Costos de Transferencia',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'import.stock.price.line',
			'context': {'default_stock_move_ids': stock_move_ids},
			'target': 'new',
		}