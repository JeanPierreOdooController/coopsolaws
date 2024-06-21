# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def action_autocomplete_partner(self):
		for statement in self:
			for line in statement.line_ids:
				move = self.env['account.move'].search([('company_id','=',line.statement_id.company_id.id),('type','=','out_invoice'),('invoice_payment_ref','=',line.ref)],limit=1)
				line.partner_id = move.partner_id.id
		return self.env['popup.it'].get_message('Se completaron los Partners.')