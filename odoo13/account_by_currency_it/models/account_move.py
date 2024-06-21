# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountMove(models.Model):
	_inherit = "account.move"

	use_account_partner_it = fields.Boolean(string='Usar Cuenta de Partner',default=False,copy=False)

	#def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
	#	t = super(AccountMove,self)._recompute_dynamic_lines(recompute_all_taxes=recompute_all_taxes,recompute_tax_base_amount=recompute_tax_base_amount)
	#	self._onchange_currency_it_account()
	#	return t

	@api.onchange('ref','currency_id','use_account_partner_it')
	def _onchange_currency_it_account(self):
		if self.type != 'entry':
			param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
			account_it = None
			if param:
				account_it = self.env['currency.parameter.line'].search([('main_parameter_id','=',param.id),('currency_id','=',self.currency_id.id)],limit=1)

			if self.is_sale_document(include_receipts=True):
				if account_it and not self.use_account_partner_it:
					new_term_account = account_it.credit_account_id
				else:
					new_term_account = self.partner_id.commercial_partner_id.property_account_receivable_id
			elif self.is_purchase_document(include_receipts=True):
				if account_it and not self.use_account_partner_it:
					new_term_account = account_it.debit_account_id
				else:
					new_term_account = self.partner_id.commercial_partner_id.property_account_payable_id
			else:
				new_term_account = None
			filtered_line = self.line_ids.filtered(lambda l: l.account_id.internal_type in ['receivable','payable'])
			filtered_line.account_id = new_term_account