# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountTransferBook(models.Model):
	_name = 'account.transfer.book'
	_description = 'Account Transfer Book'
	_auto = False
	
	cuenta = fields.Char(string='Cuenta', size=64)
	debit = fields.Float(string='Debe', digits=(64,2))
	credit = fields.Float(string='Haber', digits=(64,2))
	cta_analitica = fields.Char(string=u'Cuenta Analítica')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id, aa.code as cuenta,
				0 as debit,
				0 as credit,
				ana.name as cta_analitica,
				aa.id as account_id,
				ana.id as analytic_account_id
				from account_transfer_account_line atal
				left join account_account aa on aa.id = atal.account_id
				left join account_analytic_account ana on ana.id = atal.analytic_account_id 
				where atal.transfer_id = 0
				limit 1
			
			)''' % (self._table,)
		)