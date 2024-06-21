# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *
from io import BytesIO
import base64
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import openpyxl
except:
	install('openpyxl==3.0.5')

class AccountOpeningAdjustmentWizard(models.TransientModel):
	_name = 'account.opening.adjustment.wizard'
	_description = 'Account Opening Adjustment Wizard'	

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	journal_id = fields.Many2one('account.journal',string='Diario')
	date = fields.Date(string='Fecha Asiento')
	profit_account_id = fields.Many2one('account.account',string=u'Cuenta de Ganancias')
	loss_account_id = fields.Many2one('account.account',string=u'Cuenta de Pérdidas')
	

	def preview(self):
		self.ensure_one()
		self.env.cr.execute(self.get_sql('preview'))
		res = self.env.cr.fetchall()
		colnames = [
			desc[0] for desc in self.env.cr.description
		]
		res.insert(0, colnames)

		wb = openpyxl.Workbook()
		ws = wb.active
		row_position = 1
		col_position = 1
		for index, row in enumerate(res, row_position):
			for col, val in enumerate(row, col_position):
				ws.cell(row=index, column=col).value = val
		output = BytesIO()
		wb.save(output)
		output.getvalue()
		output_datas = base64.b64encode(output.getvalue())
		output.close()

		return self.env['popup.it'].get_file('Vista Preliminar.xlsx',output_datas)

	def get_move(self):
		self.env.cr.execute(self.get_sql('move'))
		res = self.env.cr.dictfetchall()
		lines = []
		usd = self.env.ref('base.USD')
		if not res:
			raise UserError('No existen diferencias de Tipo de Cambio')
		for elem in res:
			vals = (0,0,{
				'account_id': elem['account_id'],
				'name': elem['account_id'],
				'debit': elem['debit'],
				'credit': elem['credit'],
				'currency_id': usd.id if elem['currency'] == 'USD' else None,
				'amount_currency': 0,
				'partner_id': elem['partner_id'],
				'type_document_id': elem['type_document_id'],
				'nro_comp': elem['nro_comp'],
				'company_id': self.company_id.id,
				'tc': 1,
			})
			lines.append(vals)

		move = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': self.journal_id.id,
				'date': self.date,
				'line_ids':lines,
				'ref': 'AJUSTE TC APEERTURA',
				'glosa': 'AJUSTE POR DISTINTO TIPO DE CAMBIO EN APERTURA',
				'type':'entry'})
		
		move.action_post()

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move.id,
		}
	
	def get_sql(self,type):
		sql_account = "a1.account_id"
		sql_loss_account = "{loss_account_id} as account_id".format(loss_account_id=self.loss_account_id.id)
		sql_profit_account = "{profit_account_id} as account_id".format(profit_account_id=self.profit_account_id.id)
		sql_partner = "a1.partner_id"
		sql_type_document = "a1.type_document_id"
		if type == 'preview':
			sql_account = "c1.code as account_id"
			sql_loss_account = "'{loss_account_id}' as account_id".format(loss_account_id=self.loss_account_id.code)
			sql_profit_account = "'{profit_account_id}' as account_id".format(profit_account_id=self.profit_account_id.code)
			sql_partner = "b1.vat as partner_id"
			sql_type_document = "d1.code as type_document_id"
		sql = """
			(select   
			{sql_account},
			abs(case when a1.saldo_mn<0 then a1.saldo_mn end) as debit,
			0 as credit,
			'USD' as currency,
			0 as amount_currency,
			1 as tc,
			{sql_partner},
			{sql_type_document},
			a1.nro_comp as nro_comp,
			null as date_maturity,
			'AJUSTE POR DISTINTO TC EN APERTURA' as name,
			null as analytic_account_id,
			null as tax_ids,
			null as amount_tax
			from get_distinto_tc_apertura('{date_from}','{date_to}',{company_id}) a1
			left join res_partner b1 on b1.id=a1.partner_id
			left join account_account c1 on c1.id=a1.account_id
			left join einvoice_catalog_01 d1 on d1.id=a1.type_document_id
			where a1.haber>a1.debe
			order by c1.code,b1.name,d1.code,a1.nro_comp)

			UNION ALL

			(select 
			{profit_account_id},
			0 as debit,
			sum (abs(case when a1.saldo_mn<0 then a1.saldo_mn end)) as credit,
			'' as currency,
			0 as amount_currency,
			1 as tc,
			null as partner_id,
			null as type_document_id,
			'' as nro_comp,
			null as date_maturity,
			'AJUSTE POR DISTINTO TC EN APERTURA' as name,
			null as analytic_account_id,
			null as tax_ids,
			null as amount_tax
			from get_distinto_tc_apertura('{date_from}','{date_to}',{company_id}) a1
			where a1.haber>a1.debe)

			UNION ALL

			(select   
			{sql_account},
			0 as debit,
			case when a1.saldo_mn > 0 then a1.saldo_mn end as credit,
			'USD' as currency,
			0 as amount_currency,
			1 as tc,
			{sql_partner},
			{sql_type_document},
			a1.nro_comp as nro_comp,
			null as date_maturity,
			'AJUSTE POR DISTINTO TC EN APERTURA' as name,
			null as analytic_account_id,
			null as tax_ids,
			null as amount_tax
			from get_distinto_tc_apertura('{date_from}','{date_to}',{company_id}) a1
			left join res_partner b1 on b1.id=a1.partner_id
			left join account_account c1 on c1.id=a1.account_id
			left join einvoice_catalog_01 d1 on d1.id=a1.type_document_id
			where a1.debe > a1.haber
			order by c1.code,b1.name,d1.code,a1.nro_comp)

			UNION ALL
			(select 
			{loss_account_id},
			sum(case when a1.saldo_mn > 0 then a1.saldo_mn end) as debit,
			0 as credit,
			'' as currency,
			0 as amount_currency,
			1 as tc,
			null as partner_id,
			null as type_document_id,
			'' as nro_comp,
			null as date_maturity,
			'AJUSTE POR DISTINTO TC EN APERTURA' as name,
			null as analytic_account_id,
			null as tax_ids,
			null as amount_tax
			from get_distinto_tc_apertura('{date_from}','{date_to}',{company_id}) a1
			where a1.debe > a1.haber)
		""".format(
			sql_partner = sql_partner,
			sql_type_document = sql_type_document,
			sql_account = sql_account,
			profit_account_id = sql_profit_account,
			loss_account_id = sql_loss_account,
			company_id = self.company_id.id,
			date_from = self.period_from_id.date_start.strftime('%Y/%m/%d'),
			date_to = self.period_to_id.date_end.strftime('%Y/%m/%d')
		)

		return sql