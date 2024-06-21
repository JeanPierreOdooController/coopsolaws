# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class ConsumptionAnalysisWizardDetail(models.TransientModel):
	_name = 'consumption.analysis.wizard.detail'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True,default='pantalla')

	@api.onchange('company_id')
	def get_period(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				period = self.env['account.period'].search([('fiscal_year_id','=',fiscal_year.id),('date_start','<=',fields.Date.context_today(self)),('date_end','>=',fields.Date.context_today(self))],limit=1)
				if period:
					self.period = period
			else:
				period = self.env['account.period'].search([('date_start','<=',fields.Date.context_today(self)),('date_end','>=',fields.Date.context_today(self))],limit=1)
				if period:
					self.period = period

	def get_report(self):
		self.env.cr.execute("""DELETE FROM consumption_analysis_book_detail WHERE user_id = %d"""%(self.env.uid))
		self.env.cr.execute("""
		INSERT INTO consumption_analysis_book_detail (almacen,origen,destino,doc,date,producto,analytic_account_id,analytic_tag_id,cantidad, valor, valuation_account_id, input_account_id, user_id) 
		("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		if self.type_show == 'pantalla':
			return {
				'name': u'Análisis de Consumo - Detalle',
				'type': 'ir.actions.act_window',
				'res_model': 'consumption.analysis.book.detail',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}
		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		namefile = 'Analisis_Consumo_Detalle.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("ANALISIS DE CONSUMO DETALLE")

		worksheet.set_tab_color('blue')

		HEADERS = [u'ALMACÉN','ORIGEN','DESTINO','DOC','FECHA','PRODUCTO','CANTIDAD','VALOR','CUENTA PRODUCTO',u'CUENTA VARIACIÓN',u'CUENTA ANALÍTICA',u'ETIQUETA ANALÍTICA']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		dic = self.env['consumption.analysis.book.detail'].search([('user_id','=',self.env.uid)])

		for line in dic:
			worksheet.write(x,0,line.almacen if line.almacen else '',formats['especial1'])
			worksheet.write(x,1,line.origen if line.origen else '',formats['especial1'])
			worksheet.write(x,2,line.destino if line.destino else '',formats['especial1'])
			worksheet.write(x,3,line.doc if line.doc else '',formats['especial1'])
			worksheet.write(x,4,line.date if line.date else '',formats['dateformat'])
			worksheet.write(x,5,line.producto if line.producto else '',formats['especial1'])
			worksheet.write(x,6,line.cantidad if line.cantidad else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.valor if line.valor else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.valuation_account_id.code if line.valuation_account_id else '',formats['especial1'])
			worksheet.write(x,9,line.input_account_id.code if line.input_account_id else '',formats['especial1'])
			worksheet.write(x,10,line.analytic_account_id.name if line.analytic_account_id else '',formats['especial1'])
			worksheet.write(x,11,line.analytic_tag_id.name if line.analytic_tag_id else '',formats['especial1'])
			x += 1

		widths = [15,25,25,20,15,30,12,15,14,14,15,15]

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(u'Análisis de Consumo Detalle.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self,date_ini,date_end,company_id):
		param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		sql_inv = ""
		if param.warehouse_ids_gs:
			sql_inv = " AND GKV.almacen not in (%s)"%(','.join("'%s'"%str(i.lot_stock_id.display_name) for i in param.warehouse_ids_gs))

		sql = """SELECT
				T2.almacen,
				T2.stock_doc as doc,
				T2.fecha::date as date,
				PT.name AS producto,
				T2.origen,
				T2.destino,
				T2.analytic_account_id,
				T2.analytic_tag_id,
				T2.salida AS cantidad,
				ROUND(T2.credit,2) AS valor,
				CASE WHEN vst_valuation.account_id IS NOT NULL THEN vst_valuation.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_valuation_account WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS valuation_account_id,
				CASE WHEN vst_input.account_id IS NOT NULL THEN vst_input.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_account_input WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS input_account_id,
				{user_id} as user_id
				FROM
				(SELECT
				almacen,
				stock_doc,
				fecha,
				product_id,
				origen,
				destino,
				analytic_account_id,
				analytic_tag_id,
				COALESCE(salida,0) AS salida,
				COALESCE(credit,0) AS credit FROM
				(SELECT 
				GKV.almacen,
				GKV.stock_doc,
				GKV.fecha,
				GKV.name_template,
				GKV.product_id,
				GKV.origen,
				GKV.destino,
				GKV.salida,
				GKV.credit,
				SM.analytic_account_id,
				SM.analytic_tag_id
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				LEFT JOIN stock_location ST ON ST.id = GKV.ubicacion_origen
				LEFT JOIN stock_location ST2 ON ST2.id = GKV.ubicacion_destino
				LEFT JOIN stock_move SM on SM.id = GKV.stock_moveid
				WHERE ST.usage = 'internal' AND ST2.usage = 'production' AND (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') {sql_inv}
				UNION ALL
				SELECT 
				GKV.almacen,
				GKV.stock_doc,
				GKV.fecha,
				GKV.name_template,
				GKV.product_id,
				GKV.origen,
				GKV.destino,
				-(GKV.ingreso) AS salida,
				-(GKV.debit) AS credit,
				SM.analytic_account_id,
				SM.analytic_tag_id
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				LEFT JOIN stock_location ST ON ST.id = GKV.ubicacion_origen
				LEFT JOIN stock_location ST2 ON ST2.id = GKV.ubicacion_destino
				LEFT JOIN stock_move SM on SM.id = GKV.stock_moveid
				WHERE ST.usage = 'production' AND ST2.usage = 'internal' AND (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') {sql_inv})T)T2
				LEFT JOIN product_product PP ON PP.id = T2.product_id
				LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_valuation_account 
				WHERE company_id = {company}) vst_valuation ON vst_valuation.category_id = PT.categ_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_account_input 
				WHERE company_id = {company}) vst_input ON vst_input.category_id = PT.categ_id
		""".format(
				date_start_s = str(date_ini.year) + '0101',
				date_end_s = str(date_end).replace('-',''),
				date_ini = date_ini.strftime('%Y/%m/%d'),
				date_end = date_end.strftime('%Y/%m/%d'),
				company = company_id,
				user_id = self.env.uid,
				sql_inv = sql_inv
			)
		return sql