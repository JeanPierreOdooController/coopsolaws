# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
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

class AccountHigherRep(models.TransientModel):
	_inherit = 'account.higher.rep'

	def get_excel(self,filtro):
		print(filtro)
		self.ensure_one()
		self.env.cr.execute(self._get_sql_export())
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

		return self.env['popup.it'].get_file('Libro Mayor Analitico.xlsx',output_datas)

	def _get_sql_export(self):
		sql_accounts = "where cuenta in (%s)" % (','.join("'%s'"%(i.code) for i in self.account_ids)) if self.account_ids else ""

		if self.currency == 'pen':
			sql = """select row_number() OVER () AS id,
			periodo, fecha, libro, voucher, cuenta,
			debe, haber,balance,saldo, moneda, tc,
			code_cta_analitica, glosa, td_partner,doc_partner, partner, 
			td_sunat,nro_comprobante, fecha_doc, fecha_ven
			from get_mayor_detalle('%s','%s',%d)
			%s
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				self.company_id.id,
				sql_accounts)
		else:
			sql = """select row_number() OVER () AS id,
			periodo, fecha, libro, voucher, cuenta,
			debe_me as debe, haber_me as haber, balance_me as balance, saldo_me as saldo, moneda, tc,
			code_cta_analitica, glosa, td_partner,doc_partner, partner, 
			td_sunat,nro_comprobante, fecha_doc, fecha_ven
			from get_mayor_detalle('%s','%s',%d)
			%s
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				self.company_id.id,
				sql_accounts)
		
		return sql