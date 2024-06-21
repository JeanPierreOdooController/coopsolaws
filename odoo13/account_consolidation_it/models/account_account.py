# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAccount(models.Model):
	_inherit = "account.account"

	def action_complete_consolidation_account_ids(self):
		chart_id = self._context.get('default_chart_id')
		for account in self:
			if chart_id:
				consolidation_account = self.env['consolidation.account'].search([('chart_id','=',chart_id),('name','=',account.code)],limit=1)
				if consolidation_account:
					account.write({'consolidation_account_chart_filtered_ids': ([(6,0,[consolidation_account.id])])})
				else:
					raise UserError('no hya cuenta de consolidacioin')
			else:
				raise UserError('No hay consolidacion')
		return self.env['popup.it'].get_message(u'SE COMPLETARON LAS CUENTAS CONSOLIDADAS')