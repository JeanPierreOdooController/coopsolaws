# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class sale_order(models.Model):
	_inherit='sale.order'

	@api.model
	def _fecha_limite_vencidas(self):
		import datetime
		from dateutil.relativedelta import relativedelta
		for i in self.env['sale.order'].search([('state','!=','cancel'),('validity_date','<',datetime.datetime.now()-relativedelta(hours=5) )]).filtered(lambda r: not any([i.amount_residual ==0 for i in r.invoice_ids])):
			i.action_cancel()

class product_modelo(models.Model):
	_name = 'product.modelo'

	name = fields.Char('Modelo',required=True)


class product_familia(models.Model):
	_name = 'product.familia'

	name = fields.Char('Familia',required=True)

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	modelo = fields.Many2one('product.modelo','Modelo')
	familia = fields.Many2one('product.familia','Familia')