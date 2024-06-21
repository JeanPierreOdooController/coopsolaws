# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class FinancialSituation(models.Model):
	_name = 'financial.situation'
	_description = 'Financial Situation'
	_auto = False
	_order = 'order_balance'

	name = fields.Char(string='Nombre')
	group_balance = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_balance = fields.Integer(string='Orden')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				''::character varying as name,
				''::character varying as group_balance,
				0::numeric as total,
				0::integer as order_balance
				from get_bc_register('201900','201901',1) bcr
				limit 1
			
			)''' % (self._table,)
		)

class DynamicFinancialSituation(models.Model):
	_name = 'dynamic.financial.situation'
	_description = 'Dynamic Financial Situation'

	name = fields.Char()