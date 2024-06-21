# -*- coding: utf-8 -*-

from odoo import models, fields, api


class stockPickingNroGuiasIT(models.Model):
	_inherit = 'stock.picking'

	have_return=fields.Boolean('Tiene devoluciones')

	def action_done(self):
		res = super(stockPickingNroGuiasIT,self).action_done()
		for l in self.move_ids_without_package:
			if l.origin_returned_move_id.picking_id.id:
				self.env.cr.execute("""
					update stock_picking set have_return = true where id = """ +str(l.origin_returned_move_id.picking_id.id) + """
   				""")
			#l.origin_returned_move_id.picking_id.have_return=True
		return res
# actualizar por base de datos al instalar
# update stock_picking set have_return = true where id in (select id from stock_picking where id in (
# select picking_id from stock_move where id in (
# select origin_returned_move_id from stock_move where origin_returned_move_id is not null and state = 'done') and state = 'done')  
# and related_location_dest = 'customer')
