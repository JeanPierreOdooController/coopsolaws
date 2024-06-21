# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *
import subprocess

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from xlrd import *
except:
	install('xlrd')

class HrImportWdWizard(models.TransientModel):
	_inherit = 'hr.import.wd.wizard'

	def import_wd_template(self):
		if not self.file:
			raise UserError('Es necesario adjuntar un archivo para la importacion')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_WD.xlsx'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)
		sheet = wb.sheet_by_index(0)
		if sheet.ncols != 4:
			raise UserError('El archivo de importacion debe tener 4 columnas con la siguiente forma: \n \t EMPLEADO | CODIGO | NRO_DIAS | NRO_HORAS')
		Payslips = self.env['hr.payslip'].browse(self._context.get('payslip_ids'))
		# print("Payslips",Payslips)
		for i in range(1, sheet.nrows):
			Payslip = Payslips.filtered(lambda p: p.employee_id.identification_id == self.parse_xls_float(sheet.cell_value(i, 0)))
			if Payslip:
				WD = Payslip.worked_days_line_ids.filtered(lambda wd: wd.code == sheet.cell_value(i, 1))
				if WD:
					if WD.wd_type_id.convert_days:
						# print("number_of_hours",sheet.cell(i, 3))
						WD.number_of_hours = sheet.cell_value(i, 3)
						WD.number_of_days = sheet.cell_value(i, 3)/8
					else:
						WD.number_of_days = sheet.cell_value(i, 2)
						hour = sheet.cell_value(i, 3)
						if hour < 1:
							hour = int(hour * 24 * 3600)
							hour = time(hour//3600, (hour % 3600)//60, hour % 60)
							WD.number_of_hours = hour.hour + hour.minute/60
						else:
							WD.number_of_hours = sheet.cell_value(i, 3)

		return self.env['popup.it'].get_message('Se importaron todos los worked days satisfactoriamente')