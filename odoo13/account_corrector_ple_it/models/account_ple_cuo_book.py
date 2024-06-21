# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountPleCuoBook(models.Model):
	_name = 'account.ple.cuo.book'
	_description = 'Account Ple Cuo Book'
	_auto = False
	
	periodo = fields.Char(string='Periodo', size=50)
	fecha = fields.Date(string='Fecha Cont.')
	libro = fields.Char(string='Libro', size=5)
	fecha_doc = fields.Date(string='Fecha Em.', size=10)
	td_sunat = fields.Char(string='TD', size=64)
	nro_comprobante = fields.Char(string=u'Nro Comprobante')
	cuo = fields.Char(string=u'CUO')
	cuo_c = fields.Char(string=u'CUO Correcto')
	move_line_id = fields.Many2one('account.move.line',string=u'Apunte Contable')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				a1.periodo::character varying,a1.fecha::date,a1.libro,a1.fecha_doc,a1.td_sunat,a1.nro_comprobante, 0 as cuo,
			0 as cuo_c, a1.move_line_id
			from vst_diariog a1 limit 1
			)''' % (self._table,)
		)

	def view_account_move(self):
		return{
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_line_form').id,
			'res_model': 'account.move.line',
			'type': 'ir.actions.act_window',
			'res_id': self.move_line_id.id,
		}

	def action_fix_ple_cuo(self):
		for i in self:
			sql_update = """
				UPDATE account_move_line SET cuo = id WHERE id = %d """ % (i.move_line_id.id)

			self.env.cr.execute(sql_update)

		return self.env['popup.it'].get_message('SE ACTUALIZARON CORRECTAMENTE LOS CUOS DE LOS APUNTES SELECCIONADOS')