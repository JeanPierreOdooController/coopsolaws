# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDesDetailRangeBook(models.Model):
	_name = 'account.des.detail.range.book'
	_description = 'Account Des Detail Range Book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(12,2))
	cta_analitica = fields.Char(string=u'Cuenta Analítica')
	des_debe = fields.Char(string=u'Dest Debe') 
	des_haber = fields.Char(string=u'Dest Haber')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,a1.* FROM get_destinos_range('201900','201900',1) a1 limit 1
			
			)''' % (self._table,)
		)