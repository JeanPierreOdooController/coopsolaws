# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *

class MrpProduction(models.Model):
	_inherit = 'mrp.production'

	kardex_date = fields.Date(string="Fecha Kardex", default=lambda self: date.today() - timedelta(hours=5))
	operation_type_sunat_consume = fields.Many2one('type.operation.kardex', string="Tipo de Operacion Sunat Consumo")
	operation_type_sunat_fp = fields.Many2one('type.operation.kardex', string="Tipo de Operacion Sunat Producto Terminado")


	def update_kardex_dates(self):
		for i in self:
			i.kardex_date = datetime.now()
			move_line_ids = self.env['stock.move.line'].search(['|', ('move_id.raw_material_production_id', '=', i.id), ('move_id.production_id', '=', i.id)])
			for moves_line in move_line_ids:
				if moves_line.move_id.id:
					moves_line.move_id.with_context({'permitido':1}).write({'kardex_date': i.kardex_date })
			for elem in self.env['stock.move.line'].search([('move_id.production_id', '=', i.id)]):
				if elem.move_id.id:
					elem.move_id.with_context({'permitido':1}).write({'kardex_date':i.kardex_date + timedelta(seconds=1)})
			move_line_ids.with_context({'permitido':1}).write({'kardex_date': i.kardex_date })
			move_line_ids.refresh()
			for elem in self.env['stock.move.line'].search([('move_id.production_id', '=', i.id)]):
				elem.refresh()
				elem.with_context({'permitido':1}).write({'kardex_date':i.kardex_date + timedelta(seconds=1)})
			

	def button_mark_done(self):
		self.ensure_one()
		error = ''
		for line in self.move_raw_ids:
			if line.quantity_done > line.reserved_availability:
				raise UserError('Las cantidades consumidas no pueden ser mayor a lo reservado')

		t = super(MrpProduction, self).button_mark_done()

		self.update_kardex_dates()
		return t
