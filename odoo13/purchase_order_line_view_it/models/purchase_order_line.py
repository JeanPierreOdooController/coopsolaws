# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	default_code_product_rel = fields.Char(string='Cod Producto',related='product_id.default_code')
	name_product_rel = fields.Char(string='Producto',related='product_id.name')