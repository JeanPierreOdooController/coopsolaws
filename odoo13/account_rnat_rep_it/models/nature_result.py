# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class NatureResult(models.Model):
	_name = 'nature.result'
	_description = 'Nature Result'
	_auto = False
	_order = 'order_nature'

	name = fields.Char(string='Nombre')
	group_nature = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_nature = fields.Integer(string='Orden')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				''::character varying as name,
				''::character varying as group_nature,
				0::numeric as total,
				1::integer as order_nature
				from get_bc_register('201900','201901',1)bcr limit 1
			
			)''' % (self._table,)
		)

class DynamicNatureResult(models.Model):
	_name = 'dynamic.nature.result'
	_description = 'Dynamic Nature Result'

	name = fields.Char()