# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class CheckingRegister(models.Model):
	_name = 'checking.register'
	_description = 'Checking Register'
	_auto = False

	mayor = fields.Char(string='Mayor')
	cuenta = fields.Char(string='Cuenta')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	rubro = fields.Char(string='Rubro Estado Financiero')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id, T.mayor, T.cuenta, T.nomenclatura, T.debe, T.haber, T.saldo_deudor, T.saldo_acreedor, T.rubro
				FROM get_f1_register('201900','201901',1,'pen')T
				limit 1
			
			)''' % (self._table,)
		)