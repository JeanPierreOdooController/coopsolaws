# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class F1Register(models.Model):
	_name = 'f1.register'
	_description = 'F1 Register'
	_auto = False
	_order = 'mayor'

	period_from = fields.Char(string='Periodo Inicio')
	period_to = fields.Char(string='Periodo Final')
	mayor = fields.Char(string='Mayor')
	cuenta = fields.Char(string='Cuenta')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	activo = fields.Float(string='Activo')
	pasivo = fields.Float(string='Pasivo')
	perdinat = fields.Float(string='Perdinat')
	ganannat = fields.Float(string='Ganannat')
	perdifun = fields.Float(string='Perdifun')
	gananfun = fields.Float(string='Gananfun')
	rubro = fields.Char(string='Rubro Estado Financiero')

	def view_detail(self):
		self.env.cr.execute("""SELECT move_line_id FROM vst_diariog 
								WHERE (CAST(periodo AS int ) BETWEEN CAST('%s' AS int ) AND CAST('%s' AS int )) 
								AND cuenta = '%s'
								AND company_id = %s""" % (self.period_from,self.period_to,self.cuenta,str(self.env.company.id)))
		res = self.env.cr.dictfetchall()
		elem = []
		for key in res:
			elem.append(key['move_line_id'])

		return {
			'name': 'Detalle',
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				'201900' as period_from,
				'201901' as period_to, * FROM (
				SELECT mayor, cuenta, nomenclatura, debe, haber, saldo_deudor, saldo_acreedor, activo, pasivo, perdinat, ganannat, perdifun, gananfun, rubro
				FROM get_f1_register('201900','201901',1,'pen'))T limit 1
			
			)''' % (self._table,)
		)