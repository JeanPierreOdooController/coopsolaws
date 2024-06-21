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

class AccountDiffDestinoAnaliticaWizard(models.TransientModel):
	_name = 'account.diff.destino.analitica.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)

	def get_report(self):
		self.ensure_one()
		self.env.cr.execute("""select a2.id as aml_id,a4.id as am_id,a4.date as fecha,a5.name as diario,a4.name as asiento,a3.code as cuenta ,a2.balance as monto_conta,a1.monto  as monto_analiticas,
				abs(a2.balance)-abs(a1.monto) as diferencia 
				from 
				(
				select  move_id,sum(round(amount,2)) as monto  from account_analytic_line where company_id={company_id}
				and (date between '{date_ini}' and '{date_end}')
				group by move_id) a1

				left join account_move_line a2 on a2.id=a1.move_id
				left join account_account a3 on a3.id=a2.account_id
				left join account_move a4 on a4.id=a2.move_id
				left join account_journal a5 on a5.id=a4.journal_id
				where (abs(a2.balance)-abs(a1.monto))<>0   
				order by a4.date,a5.name,a4.name
				""".format(
					date_ini = self.date_ini.strftime('%Y/%m/%d'),
					date_end = self.date_end.strftime('%Y/%m/%d'),
					company_id = self.company_id.id
				))
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

		return self.env['popup.it'].get_file('Diferencia Analitica VS Contabiliodad.xlsx',output_datas)