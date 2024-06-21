# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class FunctionResult(models.Model):
	_name = 'function.result'
	_description = 'Function Result'
	_auto = False
	_order = 'order_function'

	name = fields.Char(string='Nombre')
	group_function = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_function = fields.Integer(string='Orden')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				''::character varying as name,
				''::character varying as group_function,
				0::numeric as total,
				1::integer order_function
				from get_bc_register('201900','201901',1) bcr limit 1
			
			)''' % (self._table,)
		)

class DynamicFunctionResult(models.Model):
	_name = 'dynamic.function.result'
	_description = 'Dynamic Function Result'

	name = fields.Char()