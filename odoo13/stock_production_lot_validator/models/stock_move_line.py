# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	lot_id_qty = fields.Float(string='Cantidad Lote', related='lot_id.product_qty')
	
class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def button_validate(self):
		# for pick in self:
		# 	if pick.picking_type_id.code == 'outgoing':
		# 		for line in pick.move_line_ids_without_package:
		# 			if line.lot_id:
		# 				default_uom = line.lot_id.product_id.uom_id
		# 				qty = default_uom._compute_quantity(line.qty_done, line.product_uom_id)
		# 				if qty > line.lot_id.product_qty:
                            
		# 					raise UserError('La cantidaddddddddddddddddd "Realizada" para el Producto %s sobrepasa la Cantidad del Lote'%(line.product_id.display_name))

		return super(StockPicking,self).button_validate()