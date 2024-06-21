# -*- coding:utf-8 -*-

from odoo import api, fields, models

class ProductProduct(models.Model):
	_inherit = 'product.product'

	def get_sale_order_wizard(self):
		wizard = self.env['sale.for.product.wizard'].create({
			'product_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_sale_for_product_wizard_form' % module)
		return {
			'name':u'Cotización por Producto',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'sale.for.product.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}