from odoo import models, api, _
from odoo.exceptions import UserError


class AccountBankStatementLine(models.Model):
	_inherit = "account.bank.statement.line"

	def button_cancel_reconciliation(self):
		t = super(AccountBankStatementLine,self).button_cancel_reconciliation()
		for line in self:
			line.move_name = None
		return t