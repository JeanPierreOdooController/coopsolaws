# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBaseCashBank(models.TransientModel):
	_name = 'account.base.cash.bank.wizard'
	_description = 'Account Base Cash Bank'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
				self.date_ini = fiscal_year.date_from
				self.date_end = fiscal_year.date_to
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Movim.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("REGISTRO")
		worksheet.set_tab_color('blue')

		HEADERS = ['ID LINEA','ID ASIENTO','PERIODO','LIBRO','ASIENTO','CUENTA','DEBE','HABER','COD BANCO','NRO CUENTA','MEDIO DE PAGO',
		'NRO OPERACION']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['id_linea'] if line['id_linea'] else '',formats['especial1'])
			worksheet.write(x,1,line['id_asiento'] if line['id_asiento'] else '',formats['especial1'])
			worksheet.write(x,2,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,3,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,4,line['asiento'] if line['asiento'] else '',formats['especial1'])
			worksheet.write(x,5,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,6,line['debe'] if line['debe'] else '',formats['numberdos'])
			worksheet.write(x,7,line['haber'] if line['haber'] else '',formats['numberdos'])
			worksheet.write(x,8,line['code_banco'] if line['code_banco'] else '',formats['especial1'])
			worksheet.write(x,9,line['nro_cuenta'] if line['nro_cuenta'] else '',formats['especial1'])
			worksheet.write(x,10,line['medio_de_pago'] if line['medio_de_pago'] else '',formats['especial1'])
			worksheet.write(x,11,line['nro_operacion'] if line['nro_operacion'] else '',formats['especial1'])
			x += 1

		widths = [12,12,11,10,10,13,10,10,15,18,11,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Movim.xlsx', 'rb')
		return self.env['popup.it'].get_file('Movimientos Caja y Banco.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self):
		sql = """SELECT * FROM base_ple_caja_bancos('%s','%s',%d)
		""" % (self.date_ini.strftime('%Y/%m/%d'),
			self.date_end.strftime('%Y/%m/%d'),
			self.company_id.id)
		return sql
	
	def domain_dates(self):
		if self.date_ini:
			if self.exercise.date_from.year != self.date_ini.year:
				raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_end:
			if self.exercise.date_from.year != self.date_end.year:
				raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_ini and self.date_end:
			if self.date_end < self.date_ini:
				raise UserError("La fecha final no puede ser menor a la fecha inicial.")