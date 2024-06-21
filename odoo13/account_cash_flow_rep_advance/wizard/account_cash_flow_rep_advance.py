# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta

class AccountCashFlowRepAdvance(models.TransientModel):
	_name = 'account.cash.flow.rep.advance'
	_description = 'Account Cash Flow Rep Advance'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	date_start = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	def get_report(self):
		if self.type_show == 'pantalla':
			self.env.cr.execute("""DELETE FROM account_cash_flow_book_advance WHERE user_id = %d"""%(self.env.uid))
		
			self.env.cr.execute("""
				INSERT INTO account_cash_flow_book_advance (journal_id,voucher,fecha,glosa,account_id,amount,grupo,concepto,user_id) 
				("""+self._get_sql()+""")""")
			
			return {
					'name': 'Reporte de Flujo de Caja',
					'type': 'ir.actions.act_window',
					'res_model': 'account.cash.flow.book.advance',
					'view_mode': 'tree,pivot,graph',
					'view_type': 'form',
				}
		else:
			parameters = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
			if parameters.use_counterpart_cash_flow:
				raise UserError('Esta función aún no está disponible')
			else:
				#raise UserError('En construccion xddd')
				import io
				from xlsxwriter.workbook import Workbook
				from xlsxwriter.utility import xl_rowcol_to_cell
				ReportBase = self.env['report.base']

				direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

				if not direccion:
					raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

				workbook = Workbook(direccion +'Flujo_Caja.xlsx')
				workbook, formats = ReportBase.get_formats(workbook)

				especial1_simple = workbook.add_format()
				especial1_simple.set_align('justify')
				especial1_simple.set_align('vcenter')
				especial1_simple.set_text_wrap()
				especial1_simple.set_font_size(10)
				especial1_simple.set_font_name('Times New Roman')

				numberdos_simple = workbook.add_format({'num_format':'0.00'})
				numberdos_simple.set_align('right')
				numberdos_simple.set_align('vcenter')
				numberdos_simple.set_font_size(10)
				numberdos_simple.set_font_name('Times New Roman')
				
				format_flujo_operativo = workbook.add_format({'bold': True})
				format_flujo_operativo.set_align('justify')
				format_flujo_operativo.set_align('vcenter')
				format_flujo_operativo.set_text_wrap()
				format_flujo_operativo.set_font_size(11)
				format_flujo_operativo.set_font_name('Times New Roman')
				format_flujo_operativo.set_bottom(6)
				format_flujo_operativo.set_top(1)

				formats['especial2'].set_underline()

				numberdosflujo_operativo = workbook.add_format({'num_format':'0.00','bold': True})
				numberdosflujo_operativo.set_align('right')
				numberdosflujo_operativo.set_align('vcenter')
				numberdosflujo_operativo.set_font_size(11)
				numberdosflujo_operativo.set_font_name('Times New Roman')
				numberdosflujo_operativo.set_bottom(6)
				numberdosflujo_operativo.set_top(1)

				import importlib
				import sys
				importlib.reload(sys)

				worksheet = workbook.add_worksheet("FLUJO CAJA")
				worksheet.set_tab_color('blue')

				HEADERS = ['CONCEPTO']
				days_arr = []
				dayi = self.date_start
				while dayi <= self.date_end:
					days_arr.append(dayi)
					dayi += timedelta(days=1)
				for i in days_arr:
					HEADERS.append(i.strftime('%d/%m/%Y'))

				worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
				x = 2

				worksheet.write(x,0,'SALDO INICIAL',especial1_simple)

				x += 2

				worksheet.write(x,0,'INGRESOS',formats['especial2'])
				x += 1

				for ingresos in self.env['account.cash.flow'].search([('grupo','=','2')]):
					worksheet.write(x,0,ingresos.code + '-' + ingresos.item,especial1_simple)
					x+= 1
				x+= 1

				worksheet.write(x,0,'EGRESOS',formats['especial2'])
				x += 1

				for egresos in self.env['account.cash.flow'].search([('grupo','=','3')]):
					worksheet.write(x,0,egresos.code + '-' + egresos.item,especial1_simple)
					x+= 1
				pos_fin_egresos = x
				x+= 2

				worksheet.write(x,0,'FLUJO OPERATIVO',format_flujo_operativo)
				pos_flujo_op = x

				x += 2

				pos_ini_finan = x

				for finan in self.env['account.cash.flow'].search([('grupo','=','4')]):
					worksheet.write(x,0,finan.code + '-' + finan.item,especial1_simple)
					x+= 1
				
				x += 1

				worksheet.write(x,0,'INDEFINIDO',especial1_simple)
				pos_fin_finan = x

				x += 2

				worksheet.write(x,0,'SALDO FINAL',format_flujo_operativo)

				pos_saldo_final = x

				y = 1

				for day_i in days_arr: 
					x = 2
					if day_i == self.date_start:
						worksheet.write(x,y,self.get_saldo(datetime.strptime('%d/01/01'%(self.date_start.year), '%Y/%m/%d').date(),day_i - timedelta(days=1),False),numberdos_simple)
					else:
						worksheet.write_formula(x,y, '=' + xl_rowcol_to_cell(pos_saldo_final,y-1), numberdos_simple)
					x += 3

					for ingresos in self.env['account.cash.flow'].search([('grupo','=','2')]):
						worksheet.write(x,y,self.get_saldo(day_i,day_i,True,ingresos.id),numberdos_simple)
						x+= 1

					x += 2

					for egresos in self.env['account.cash.flow'].search([('grupo','=','3')]):
						worksheet.write(x,y,self.get_saldo(day_i,day_i,True,egresos.id),numberdos_simple)
						x+= 1
					x += 2
					
					worksheet.write_formula(x,y, '=sum(' + xl_rowcol_to_cell(2,y) +':' +xl_rowcol_to_cell(pos_fin_egresos,y) + ')', numberdosflujo_operativo)
					x += 2

					for finan in self.env['account.cash.flow'].search([('grupo','=','4')]):
						worksheet.write(x,y,self.get_saldo(day_i,day_i,True,finan.id),numberdos_simple)
						x+= 1
					x += 1
					worksheet.write(x,y,self.get_saldo(day_i,day_i,True),numberdos_simple)
					x+=2
					worksheet.write_formula(x,y, '='+ xl_rowcol_to_cell(pos_flujo_op,y) +'+sum(' + xl_rowcol_to_cell(pos_ini_finan,y) +':' +xl_rowcol_to_cell(pos_fin_finan,y) + ')', numberdosflujo_operativo)
					y+=1
				
				widths = [26]
				for day_i in days_arr:
					widths.append(11)
				worksheet = ReportBase.resize_cells(worksheet,widths)
				workbook.close()

				f = open(direccion +'Flujo_Caja.xlsx', 'rb')
				return self.env['popup.it'].get_file('Flujo de Caja de %s al %s.xlsx'%(self.date_start.strftime('%Y/%m/%d'),self.date_end.strftime('%Y/%m/%d')),base64.encodestring(b''.join(f.readlines())))

				



	def get_saldo(self,date_start,date_end,filtro,flujo_id=None):
		if date_end < date_start:
			return 0
		sql = """select sum(aml.balance) as amount from account_move_line aml
				left join account_move am on am.id = aml.move_id
				left join account_account aa on aa.id = aml.account_id
				where (am.date between '%s' and '%s') and left(aa.code,2) = '10' and am.company_id = %d
				%s"""%(date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				self.company_id.id, 
				(" and aml.cash_flow_id = %d"%(flujo_id) if flujo_id else " and aml.cash_flow_id is null") if filtro else "")
		self.env.cr.execute(sql)
		res =self.env.cr.fetchone()
		return res[0] if res else 0


	def _get_sql(self):
		parameters = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)

		if not parameters:
			raise UserError('Faltan configurar los Parametros Principales para esta Compañía')
		if not parameters.use_counterpart_cash_flow:
			sql = """SELECT 
					T.journal_id,
					T.voucher,
					T.fecha,
					T.glosa,
					T.account_id,
					T.amount,
					CASE WHEN T.grupo = '1' THEN '1-SALDO INICIAL'
					WHEN T.grupo = '2' THEN '2-INGRESO'
					WHEN T.grupo = '3' THEN '3-EGRESO'
					WHEN T.grupo = '4' THEN '4-FLUJO OPERATIVO' END AS grupo,
					T.concepto,
					%d as user_id
					FROM (SELECT 
					am.journal_id,
					am.name as voucher,
					am.date as fecha,
					am.glosa,
					aml.account_id,
					coalesce(aml.debit) - coalesce(aml.credit) as amount,
					acf.grupo,
					acf.code,
					acf.code||'-'||acf.item as concepto
					FROM account_move_line aml
					LEFT JOIN account_account aa ON aa.id = aml.account_id
					LEFT JOIN account_cash_flow acf ON acf.id = aml.cash_flow_id
					LEFT JOIN account_move am ON am.id = aml.move_id
					WHERE LEFT(aa.code,2) = '10' AND aml.cash_flow_id IS NOT NULL AND am.state = 'posted' AND
					am.company_id = %d AND aml.display_type IS NULL
					AND (am.date BETWEEN '%s' AND '%s'))T
					ORDER BY T.grupo,T.code
			""" % (self.env.uid,
				self.company_id.id,
				self.date_start.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'))

		else:
			sql = """
				SELECT 
				T.journal_id,
				T.voucher,
				T.fecha,
				T.glosa,
				T.account_id,
				T.amount,
				CASE WHEN T.grupo = '1' THEN '1-SALDO INICIAL'
				WHEN T.grupo = '2' THEN '2-INGRESO'
				WHEN T.grupo = '3' THEN '3-EGRESO'
				WHEN T.grupo = '4' THEN '4-FINANCIAMIENTO' END AS grupo,
				T.concepto,
				%d as user_id FROM
				(SELECT 
				am.journal_id,
				am.name as voucher,
				am.date as fecha,
				am.glosa,
				aml.account_id,
				(aml.balance)*-1 as amount,
				acf.grupo,
				acf.code,
				acf.code||'-'||acf.item as concepto
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_cash_flow acf ON acf.id = aa.account_cash_flow_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE LEFT(aa.code,2) <> '10' AND aa.account_cash_flow_id IS NOT NULL AND aml.move_id in (
				SELECT
				DISTINCT ON (aml.move_id) move_id
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE am.state = 'posted' AND am.company_id = %d AND aml.display_type IS NULL AND am.is_opening_close <> TRUE 
				AND (am.date BETWEEN '%s' AND '%s')
				AND LEFT(aa.code,2) = '10'))T
				ORDER BY T.grupo,T.code
			"""% (self.env.uid,
				self.company_id.id,
				self.date_start.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'))
		
		return sql