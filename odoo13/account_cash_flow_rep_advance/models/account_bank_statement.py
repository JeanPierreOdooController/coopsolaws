# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	account_cash_flow_id = fields.Many2one('account.cash.flow',string='Tipo Flujo de Caja')

	def _prepare_reconciliation_move_line(self, move, amount):
		aml_dict = super(AccountBankStatementLine,self)._prepare_reconciliation_move_line(move, amount)
		aml_dict['cash_flow_id'] = self.account_cash_flow_id.id
		return aml_dict