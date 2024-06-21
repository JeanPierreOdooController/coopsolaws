# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDesMove(models.Model):
	_name = 'account.des.move'
	_description = 'Account Des Move'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
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
				SELECT row_number() OVER () AS id, * from vst_destinos where am_id = 0 limit 1
			
			)''' % (self._table,)
		)