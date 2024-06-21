# -- coding: utf-8 --

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPleCuoWizard(models.TransientModel):
	_name = 'account.ple.cuo.wizard'
	_description = 'Account Ple Cuo Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	lines = fields.One2many('account.ple.cuo.wizard.book','main_id',string='Lineas')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		self._cr.execute(self._get_sql())
		res = self._cr.dictfetchall()
		obj = self.env['account.ple.cuo.wizard.book']
		self.lines.unlink()
		for line in res:
			obj.create({
				'main_id': self.id,
				'periodo': line['periodo'],
				'fecha': line['fecha'],
				'libro': line['libro'],
				'fecha_doc': line['fecha_doc'],
				'td_sunat': line['td_sunat'],
				'nro_comprobante': line['nro_comprobante'],
				'cuo': line['cuo'],
				'cuo_c': line['cuo_c'],
				'move_line_id': line['move_line_id']
			})

		return {
			'type': 'ir.actions.act_window',
			'res_model': 'account.ple.cuo.wizard',
			'view_mode': 'form',
			'res_id': self.id,
			'views': [(False, 'form')],
			'target': 'new',
		}
	 
	def fix_lines(self):
		for i in self.lines:
			sql_update = """
				UPDATE account_move_line SET cuo = id WHERE id = %d """ % (i.move_line_id.id)

			self.env.cr.execute(sql_update)

		return self.env['popup.it'].get_message('SE ACTUALIZARON CORRECTAMENTE LOS CUOS DE LOS APUNTES SELECCIONADOS')

	def _get_sql(self):
		sql = """
			select t.* from (
			select a1.periodo::character varying,a1.fecha::date,a1.libro,a1.fecha_doc,a1.td_sunat,a1.nro_comprobante,aml.cuo,
			aml.id as cuo_c, a1.move_line_id
			from vst_diariog a1
			left join account_move_line aml on aml.id = a1.move_line_id
			where a1.periodo = '%s'
			and a1.company_id = %d) t
			where t.cuo<>t.cuo_c
		""" % (self.period.code, self.company_id.id)

		return sql

class AccountPleCuoWizardBook(models.TransientModel):
	_name = 'account.ple.cuo.wizard.book'
	_description = 'Account Ple Cuo Wizard Book'
	
	main_id = fields.Many2one('account.ple.cuo.wizard',string='Wizard')
	periodo = fields.Char(string='Periodo', size=50)
	fecha = fields.Date(string='Fecha Cont.')
	libro = fields.Char(string='Libro', size=5)
	fecha_doc = fields.Date(string='Fecha Em.', size=10)
	td_sunat = fields.Char(string='TD', size=64)
	nro_comprobante = fields.Char(string=u'Nro Comprobante')
	cuo = fields.Char(string=u'CUO')
	cuo_c = fields.Char(string=u'CUO Correcto')
	move_line_id = fields.Many2one('account.move.line',string=u'Apunte Contable')