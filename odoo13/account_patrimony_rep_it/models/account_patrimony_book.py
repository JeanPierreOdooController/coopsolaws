# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountPatrimonyBook(models.Model):
	_name = 'account.patrimony.book'
	_description = 'Account Patrimony Book'
	_auto = False
	
	glosa = fields.Text(string='Conceptos')
	capital = fields.Float(string='Capital', digits=(64,2))
	acciones = fields.Float(string='Acciones de Inversion', digits=(64,2))
	cap_add = fields.Float(string='Capital Adicional', digits=(64,2))
	res_no_real = fields.Float(string='Resultados no Realizados', digits=(64,2))
	exce_de_rev = fields.Float(string='Excedente de Revaluacion', digits=(64,2))
	reservas = fields.Float(string='Reservas', digits=(64,2))
	res_ac = fields.Float(string='Resultados Acumulados', digits=(64,2))
	total = fields.Float(string='Totales', digits=(64,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				a1.glosa, 0::numeric as capital, 0::numeric as acciones, 0::numeric as cap_add, 0::numeric as res_no_real,
				0::numeric as exce_de_rev, 0::numeric as reservas, 0::numeric as res_ac, 0::numeric as total
				FROM vst_diariog a1 limit 1
			
			)''' % (self._table,)
		)