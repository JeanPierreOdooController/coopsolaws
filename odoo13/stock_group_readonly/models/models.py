# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
	_inherit = 'stock.quant'

	can_edit_inventory_quantity = fields.Boolean(compute='_compute_can_edit_inventory_quantity')

	@api.depends('product_id')
	def _compute_can_edit_inventory_quantity(self):
		group = self.env.ref('stock_group_readonly.aditional_edit_inventory_quantity')
		for record in self:
			# Comprueba si el usuario actual pertenece al grupo
			record.can_edit_inventory_quantity = group.id in self.env.user.groups_id.ids
