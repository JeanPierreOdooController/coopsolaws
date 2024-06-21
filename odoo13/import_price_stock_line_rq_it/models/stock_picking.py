from odoo import models, fields, exceptions, api, _
from odoo.exceptions import Warning, UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	def action_wizard(self):
		for i  in self:
			if i.picking_type_id.code =='incoming':
				return {
					'name': 'Actualizador de Costos de Transferencia',
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'import.stock.price.line',
					'context': {'default_picking_id': self.id},
					'target': 'new',
				}
			else:
				raise UserError (u"El Importador de Costos de Tranferencia solo esta disponible en los tipo de operación RECIBO")