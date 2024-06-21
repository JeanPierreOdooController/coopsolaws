from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	currency_id_book = fields.Many2one(related='move_id.currency_id', readonly=True, string='Currency Book')
	acc_number_partner_id_book = fields.Many2one(related='move_id.acc_number_partner_id', readonly=True)
	bank_id_book = fields.Many2one(related='move_id.acc_number_partner_id.bank_id', readonly=True)
	invoice_payment_term_id_book = fields.Many2one(related='move_id.invoice_payment_term_id', readonly=True)
	invoice_payment_ref_book = fields.Char(related='move_id.invoice_payment_ref', string="Referencia de Pago", store=True,readonly=True)

	def name_get(self):
		result = []
		for move_line in self:
			name = move_line.nro_comp if move_line.nro_comp else '/'
			result.append((move_line.id, name))
		return result