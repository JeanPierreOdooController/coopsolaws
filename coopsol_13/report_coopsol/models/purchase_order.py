# -*- coding:utf-8 -*-

from odoo import api, fields, models

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	def get_purchase_order_print_wizard(self):
		wizard = self.env['purchase.order.print.wizard'].create({
			'purchase_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_purchase_order_print_wizard_form' % module)
		return {
			'name':u'Modo Impresión',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'purchase.order.print.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}