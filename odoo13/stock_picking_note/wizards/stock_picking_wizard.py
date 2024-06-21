# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
# from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class StockPickingWizard(models.TransientModel):
	_name = 'stock.picking.wizard'

	name = fields.Char()
	guide_number = fields.Char(string='Numero de Guia para Anular')	
	cancel_reason = fields.Selection([('print_error','Error de Impresion'),
									('return','Devolucion')],string='Motivo de Anulacion')
	cancel_date = fields.Date(string=u'Fecha de Anulación',default=lambda self:date.today())

	def cancel_guide(self):
		picking = self.env['stock.picking'].browse(self.env.context['active_id'])
		
		self.env['stock.picking.anulation.line'].create({
														'picking_id':picking.id,
														'guide_number':self.guide_number,
														'cancel_reason':self.cancel_reason,
														'cancel_date':self.cancel_date,
														'res_user_id':self._uid
														})
		if picking.serie_guia and self.cancel_reason == 'print_error':
			picking.numberg = picking.serie_guia.next_by_id()
		wizard = self.env['stock.return.picking'].create({})
		if self.cancel_reason == 'return':
			picking.canceled_guide = True
			wizard._onchange_pickin()
			context = self._context or {}
			return {
				'type':'ir.actions.act_window',
				'res_id':wizard.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'stock.return.picking',
				'views':[[self.env.ref('stock.view_stock_return_picking_form').id,'form']],
				'target':'new',
				'context':context
			}
	

class StockReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'

	def _create_returns(self):
		context_c = self.env.context.copy()
		context_c["permitido"] = True
		new_picking_id, picking_type_id = super(StockReturnPicking,self)._create_returns()
		new_picking = self.env['stock.picking'].search([('id', '=', new_picking_id)], limit=1)
		new_picking.canceled_guide = False
		new_picking.serie_guia = None
		new_picking.carrier_id_it = None
		new_picking.vehicle_id = None
		new_picking.driver_id = None
		new_picking.starting_point = self.picking_id.ending_point
		new_picking.ending_point = self.picking_id.starting_point
		new_picking.with_context(context_c).kardex_date = None
		new_picking.numberg = None
		param = self.env['main.parameter'].search([])[0]
		if param.anular_albaranres_view:
			new_picking.with_context(context_c).no_mostrar = True
			self.picking_id.with_context(context_c).no_mostrar = True
		#Falta Tipo Doc SUNAT 
		return new_picking_id, picking_type_id

	def _onchange_pickin(self):
		move_dest_exists = False
		product_return_moves = [(5,)]
		if self.picking_id and self.picking_id.state != 'done':
			raise UserError(_("You may only return Done pickings."))
        # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
        # default values for creation.
		line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
		product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
		for move in self.picking_id.move_lines:
			if move.state == 'cancel':
				continue
			if move.scrapped:
				continue
			if move.move_dest_ids:
				move_dest_exists = True
			product_return_moves_data = dict(product_return_moves_data_tmpl)
			product_return_moves_data.update(self._prepare_stock_return_picking_line_vals_from_move(move))
			product_return_moves.append((0, 0, product_return_moves_data))
		if self.picking_id and not product_return_moves:
			raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
		if self.picking_id:
			product_return_moves.pop(0)
			ids = []
			for mm in product_return_moves:
				ids.append(mm[2]['move_id'])

			temp_move_ids = self.env['stock.move'].search( [('id', 'in', ids)] )
			temp_ids = []
			for temp in temp_move_ids:
				if temp.state == 'done':
					temp_ids.append(temp.id)
					temp.state = 'assigned'
			# raise UserError(_(str(product_return_moves) + '           ' + str(self.product_return_moves)))
			self.product_return_moves = product_return_moves
			temp_move_ids = self.env['stock.move'].search( [('id', 'in', temp_ids)] )
			for temp in temp_move_ids:
				if temp.state == 'assigned':
					temp.state = 'done'
			
			self.move_dest_exists = move_dest_exists
			self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
			self.original_location_id = self.picking_id.location_id.id
			location_id = self.picking_id.location_id.id
			if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
				location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
			self.location_id = location_id
