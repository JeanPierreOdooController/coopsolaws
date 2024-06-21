# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDesGenerateBook(models.Model):
	_name = 'account.des.generate.book'
	_description = 'Account Des Generate Book'
	_auto = False
	
	periodo = fields.Char(string='Periodo')
	glosa = fields.Text(string='Glosa')
	cuenta = fields.Char(string='Cuenta', size=64)
	name = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id, a1.periodo, a1.glosa, a1.cuenta, a1.name, a1.debe, a1.haber from get_asiento_destino('201900',1) a1 limit 1
			
			)''' % (self._table,)
		)