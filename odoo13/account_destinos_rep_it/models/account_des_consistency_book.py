# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDesConsistencyBook(models.Model):
	_name = 'account.des.consistency.book'
	_description = 'Account Des Consistency Book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,d1.periodo,d1.libro,d1.voucher,d1.cuenta,d1.debe,d1.haber
				from vst_diariog d1 limit 1
			
			)''' % (self._table,)
		)