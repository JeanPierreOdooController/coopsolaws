# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
	_inherit = 'product.product'

	characteristic_line_ids = fields.One2many('product.line.characteristic','product_id',string=u'Características')

class ProductLineCharacteristic(models.Model):
	_name = 'product.line.characteristic'

	product_id = fields.Many2one('product.product',string='Producto')
	description = fields.Char(string=u'Característica')