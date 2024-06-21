# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class F1Balance(models.Model):
	_name = 'f1.balance'
	_description = 'F1 Balance'
	_auto = False
	_order = 'mayor'

	period_from = fields.Char(string='Periodo Inicio')
	period_to = fields.Char(string='Periodo Final')
	mayor = fields.Char(string='Mayor')
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

	def view_detail(self):
		self.env.cr.execute("""SELECT move_line_id FROM vst_diariog 
								WHERE (CAST(periodo AS int ) BETWEEN CAST('%s' AS int ) AND CAST('%s' AS int )) 
								AND left(cuenta,2) = '%s'
								AND company_id = %s""" % (self.period_from,self.period_to,self.mayor,str(self.env.company.id)))
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
				SELECT *
				FROM get_f1_balance('201900','201901',1,'pen'))T limit 1
			
			)''' % (self._table,)
		)