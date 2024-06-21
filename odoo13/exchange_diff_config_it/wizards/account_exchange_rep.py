# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountExchangeRep(models.TransientModel):
	_name = 'account.exchange.rep'
	_description = 'Account Exchange Rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string=u'Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view account_exchange_book as ("""+self._get_sql_report(self.fiscal_year_id.name,self.period,self.company_id.id)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Registro Diferencia ME Global',
				'type': 'ir.actions.act_window',
				'res_model': 'account.exchange.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def do_invoice(self):
		move_id_global = self.env['exchange.diff.config.line'].search([('period_id','=',self.period.id),('line_id.company_id','=',self.company_id.id)],limit=1).move_id_global
		if move_id_global:
			if move_id_global.state =='draft':
				pass
			else:
				for mm in move_id_global.line_ids:
					mm.remove_move_reconcile()
				move_id_global.button_cancel()
			move_id_global.line_ids.unlink()
			move_id_global.name = "/"
			move_id_global.unlink()

		dt_perception = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dt_perception
		destination_journal = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal

		if not destination_journal:
			raise UserError(u'No existe un Diario Asiento Automático configurado en Parametros Generales de Contabilidad para su Compañía.')

		profit_account_id = self.env['exchange.diff.config'].search([('company_id','=',self.company_id.id)],limit=1).profit_account_id
		loss_account_id = self.env['exchange.diff.config'].search([('company_id','=',self.company_id.id)],limit=1).loss_account_id

		sql = """SELECT * FROM get_saldos_me_global_final('%s','%s',%d)""" % (self.fiscal_year_id.name,self.period.code,self.company_id.id)
		self.env.cr.execute(sql)
		obj =self.env.cr.fetchall()
		if len(obj) == 0:
			raise UserError('No existen diferencias de cambio en el periodo %s'%(self.period.name))
		lineas = []
		sum_credit = 0
		sum_debit = 0
		currency = self.env.ref('base.USD')
		for elemnt in obj:
			vals = (0,0,{
				'account_id': elemnt[0],
				'name': 'DIFERENCIA DE CAMBIO '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
				'debit': 0 if elemnt[8] > 0 else abs(elemnt[8]),
				'credit': 0 if elemnt[8] < 0 else abs(elemnt[8]),
				'amount_currency': 0,
				'currency_id': currency.id,
				'type_document_id': dt_perception.id,
				'nro_comp': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
				'tc':1,
				'company_id': self.company_id.id,
			})
			sum_credit+= 0 if elemnt[8] < 0 else abs(elemnt[8])
			sum_debit+= 0 if elemnt[8] > 0 else abs(elemnt[8])
			lineas.append(vals)

		if sum_credit != 0:
			vals_loss = (0,0,{
					'account_id': loss_account_id.id,
					'name': 'DIFERENCIA DE CAMBIO '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'debit': sum_credit,
					'credit': 0,
					'amount_currency': 0,
					'currency_id': currency.id,
					'type_document_id': dt_perception.id,
					'nro_comp': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'tc':1,
					'company_id': self.company_id.id,
				})
			lineas.append(vals_loss)

		if sum_debit != 0:
			vals_profit = (0,0,{
					'account_id': profit_account_id.id,
					'name': 'DIFERENCIA DE CAMBIO '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'debit': 0,
					'credit': sum_debit,
					'amount_currency': 0,
					'currency_id': currency.id,
					'type_document_id': dt_perception.id,
					'nro_comp': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'tc':1,
					'company_id': self.company_id.id,
				})
			lineas.append(vals_profit)
		
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': destination_journal.id,
			'date': self.period.date_end,
			'ref': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
			'glosa': 'DIFERENCIA DE CAMBIO DE '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
			'line_ids':lineas})

		if move_id.state == "draft":
			move_id.post()

		sql_update = """
					UPDATE exchange_diff_config_line
					SET move_id_global = %s
					WHERE id = (
						select e.id from exchange_diff_config_line e
						left join exchange_diff_config edc on edc.id = e.line_id
						where company_id = %s and period_id = %s
						limit 1
					)
				""" % (str(move_id.id),str(self.company_id.id),str(self.period.id))

		self.env.cr.execute(sql_update)

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Diferencia_ME_Global.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DIFERENCIA ME GLOBAL############
		worksheet = workbook.add_worksheet("DIFERENCIA ME GLOBAL")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','CUENTA','DEBE','HABER','SALDO MN','SALDO ME','TC','SALDO ACT','DIFERENCIA','CTA DIFERENCIA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.exchange.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,3,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,4,line.saldomn if line.saldomn else '0.00',formats['numberdos'])
			worksheet.write(x,5,line.saldome if line.saldome else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,7,line.saldo_act if line.saldo_act else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.diferencia if line.diferencia else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.cuenta_diferencia if line.cuenta_diferencia else '',formats['especial1'])
			x += 1

		widths = [10,12,12,12,15,15,5,15,15,20]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Diferencia_ME_Global.xlsx', 'rb')
		return self.env['popup.it'].get_file('Diferencia_ME_Global.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql_report(self,fiscal_year,period,company_id):

		sql = """SELECT 
				row_number() OVER () AS id,
				'%s' as periodo,
				aa.code as cuenta,
				gsm.debe,
				gsm.haber,
				gsm.saldomn,
				gsm.saldome,
				gsm.tc,
				gsm.saldo_act,
				gsm.diferencia,
				aa2.code as cuenta_diferencia,
				gsm.account_id,
				%d as period_id
				FROM get_saldos_me_global_final('%s','%s',%d) gsm
				LEFT JOIN account_account aa ON aa.id = gsm.account_id
				LEFT JOIN account_account aa2 ON aa2.id = gsm.difference_account_id
			""" % (period.code,
				period.id,
				fiscal_year,
				period.code,
				company_id)

		return sql