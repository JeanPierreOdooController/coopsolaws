# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import UserError


class AccountPayment(models.Model):
	_inherit = "account.payment"

	def personalize_currency_rate(self):
		for pay in self:
			for line in pay.move_line_ids:
				line.write({'tc': pay.type_change})
				line.move_id.write({'currency_rate': pay.type_change})
				if pay.currency_id.name == 'PEN':
					if line.currency_id:
						self.env.cr.execute("UPDATE account_move_line SET amount_currency = %s WHERE id = %s" % (str(round(pay.amount/pay.type_change,2)),str(line.id)))
				if pay.currency_id.name == 'USD':
					self.env.cr.execute("UPDATE account_move_line SET debit = "+str(round(pay.amount*pay.type_change,2))+" WHERE amount_currency>0 and payment_id = "+str(pay.id))
					self.env.cr.execute("UPDATE account_move_line SET credit = "+str(round(pay.amount*pay.type_change,2))+" WHERE amount_currency<0 and payment_id = "+str(pay.id))