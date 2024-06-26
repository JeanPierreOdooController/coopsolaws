# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDesSummaryBook(models.Model):
	_name = 'account.des.summary.book'
	_description = 'Account Des Summary Book'
	_auto = False
	
	cuenta = fields.Char(string='Cuenta', size=64)
	balance = fields.Float(string='Balance', digits=(12,2))
	cta20 = fields.Float(string='Cta 20', digits=(12,2))
	cta24 = fields.Float(string='Cta 24', digits=(12,2))
	cta25 = fields.Float(string='Cta 25', digits=(12,2))
	cta26 = fields.Float(string='Cta 26', digits=(12,2))
	cta90 = fields.Float(string='Cta 90', digits=(12,2))
	cta91 = fields.Float(string='Cta 91', digits=(12,2))
	cta92 = fields.Float(string='Cta 92', digits=(12,2))
	cta93 = fields.Float(string='Cta 93', digits=(12,2))
	cta94 = fields.Float(string='Cta 94', digits=(12,2))
	cta95 = fields.Float(string='Cta 95', digits=(12,2))
	cta96 = fields.Float(string='Cta 96', digits=(12,2))
	cta97 = fields.Float(string='Cta 97', digits=(12,2))
	cta98 = fields.Float(string='Cta 98', digits=(12,2))
	cta99 = fields.Float(string='Cta 99', digits=(12,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,a1.* FROM get_summary_destinos('201900',1) a1 limit 1
			
			)''' % (self._table,)
		)