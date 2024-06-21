# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	landed_cost_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado')

	def add_to_landed_cost(self):
		vals=[]
		for line in self.line_ids:
			if line.product_id.is_landed_cost:
				val = {
					'landed_id': self.landed_cost_id.id,
					'invoice_id': line.id,
					'invoice_date': line.move_id.invoice_date,
					'type_document_id': line.type_document_id.id,
					'nro_comp': line.nro_comp,
					'date': line.move_id.date,
					'partner_id': line.partner_id.id,
					'product_id': line.product_id.id,
					'debit': line.debit,
					'amount_currency': line.amount_currency,
					'tc': line.tc,
					'company_id': line.company_id.id,
				}
				vals.append(val)
		self.env['landed.cost.invoice.line'].create(vals)
		self.landed_cost_id._change_flete()
		return self.env['popup.it'].get_message(u'SE AGREGARON AL GASTO VINCULADO.')