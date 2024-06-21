# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import base64

class ReportFichaTrabajador(models.TransientModel):
	_name = "report.ficha.trabajador"
	_description = "Reporte Ficha Trabajador"

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	# type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],default='pantalla',string=u'Mostrar en', required=True)
	# payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	employees_ids = fields.Many2many('hr.employee','rel_ficha_trabajador_employee','employee_id','report_id','Empleados')
	allemployees = fields.Boolean('Todos los Empleados',default=True)

	def get_all(self):
		# self.domain_dates()
		option=0
		return self.get_excel(option)

	def get_journals(self):
		# self.domain_dates()
		if self.allemployees == False:
			option=1
			return self.get_excel(option)
		else:
			raise UserError('Debe escoger al menos un Empleado.')

	def get_excel(self,option):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Reporte_historico_empleados.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Historico Empleados")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])
		worksheet.merge_range(3, 1, 3, 8, "*** REPORTE HISTORICO DE EMPLEADOS ***", formats['especial5'])

		x, y = 5, 0

		# estilo personalizado
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		# boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#99CCFF')

		dateformat = workbook.add_format({'num_format':'dd-mm-yyyy'})
		dateformat.set_align('center')
		dateformat.set_align('vcenter')
		# dateformat.set_border(style=1)
		dateformat.set_font_size(8)
		dateformat.set_font_name('Times New Roman')

		formatCenter = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'center', 'font_size': 8})
		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)

		HEADERS = ['Nombres','Apellido Paterno','Apellido Materno','Tipo Documento','N° Documento','Fecha Nacimiento','Edad','Fecha Ingreso',
				   'Fecha Cese','Area','Cargo','Modelo Contrato','Mail','Sexo','Motivo Cese','Inactivo','Codigo Centro Costo',
				   'Nombre Centro Costo','Nivel Instruccion','Estado Civil','Regimen Pension','Tipo de Comision','CUSPP','Salario',
				   'Asig. Fam.','Banco Remuneracion','Moneda','Cuenta Remuneraciones','Banco CTS','Moneda CTS',
				   'Cuenta CTS','Tipo Trabajador','Situacion Trabajador', 'Regimen Laboral','Compañia','Direccion','Telefono']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,y,boldbord)
		x += 1

		if option == 1:
			# print("employees_ids",tuple(self.employees_ids.mapped('id')))
			employees = self.env['hr.employee'].search([('id','in',tuple(self.employees_ids.mapped('id')))])
		else:
			employees = self.env['hr.employee'].search([])

		for c, employee_id in enumerate(employees, 1):
			last_contract = self.env['hr.contract'].search([('employee_id','=', employee_id.id),('state','in',('open','close'))],
														   order='create_date desc', limit=1)
			first_contract = self.env['hr.contract'].get_first_contract(employee_id, last_contract)

			if employee_id.birthday:
				edad = date.today().year - employee_id.birthday.year
				cumpleanios = employee_id.birthday + relativedelta(years=edad)
				if cumpleanios > date.today():
					edad = edad - 1
				age = edad
			else:
				age = False

			worksheet.write(x, 0, employee_id.names if employee_id.names else '', formatLeft)
			worksheet.write(x, 1, employee_id.last_name if employee_id.last_name else '', formatLeft)
			worksheet.write(x, 2, employee_id.m_last_name if employee_id.m_last_name else '', formatLeft)
			worksheet.write(x, 3, employee_id.type_document_id.name if employee_id.type_document_id.name else '', formatCenter)
			worksheet.write(x, 4, employee_id.identification_id if employee_id.identification_id else '', formatCenter)
			worksheet.write(x, 5, employee_id.birthday if employee_id.birthday else '', dateformat)
			worksheet.write(x, 6, str(age) if age else '', formatCenter)
			worksheet.write(x, 7, first_contract.date_start if first_contract.date_start else '', dateformat)
			worksheet.write(x, 8, last_contract.date_end if last_contract.date_end else '', dateformat)
			# worksheet.write(x, 9, employee_id.sucursal_id.name if employee_id.sucursal_id.name else '', formatLeft)
			worksheet.write(x, 9, employee_id.department_id.name if employee_id.department_id.name else '', formatLeft)
			worksheet.write(x, 10, employee_id.job_id.name if employee_id.job_id.name else '', formatLeft)
			worksheet.write(x, 11, last_contract.contract_type_id.name if last_contract.contract_type_id.name else '', formatLeft)
			worksheet.write(x, 12, employee_id.work_email if employee_id.work_email else '', formatLeft)
			worksheet.write(x, 13, dict(employee_id._fields['gender'].selection).get(employee_id.gender) if employee_id.gender else '', formatLeft)
			worksheet.write(x, 14, last_contract.situation_reason_id.name if last_contract.situation_reason_id.name else '', formatLeft)
			worksheet.write(x, 15, 'NO' if employee_id.active else 'SI', formatLeft)
			worksheet.write(x, 16, last_contract.distribution_id.name if last_contract.distribution_id.name else '', formatLeft)
			worksheet.write(x, 17, last_contract.distribution_id.description if last_contract.distribution_id.description else '', dateformat)
			worksheet.write(x, 18, dict(employee_id._fields['certificate'].selection).get(employee_id.certificate) if employee_id.certificate else '', formatLeft)
			worksheet.write(x, 19, dict(employee_id._fields['marital'].selection).get(employee_id.marital) if employee_id.marital else '', formatLeft)
			worksheet.write(x, 20, last_contract.membership_id.name if last_contract.membership_id.name else '', formatLeft)
			worksheet.write(x, 21, dict(last_contract._fields['commision_type'].selection).get(last_contract.commision_type) if last_contract.commision_type else '', formatLeft)
			worksheet.write(x, 22, last_contract.cuspp if last_contract.cuspp else '', formatLeft)
			worksheet.write(x, 23, last_contract.wage if last_contract.wage else 0.0, numberdos)
			worksheet.write(x, 24, 102.50 if employee_id.children>0 else 0.0, numberdos)
			worksheet.write(x, 25, employee_id.bank_export_paymet.name if employee_id.bank_export_paymet.name else '', formatLeft)
			worksheet.write(x, 26, employee_id.wage_bank_account_id.currency_id.name if employee_id.wage_bank_account_id.currency_id else '', formatLeft)
			worksheet.write(x, 27, employee_id.wage_bank_account_id.acc_number if employee_id.wage_bank_account_id.acc_number else '', formatLeft)
			worksheet.write(x, 28, employee_id.bank_export_cts.name if employee_id.bank_export_cts.name else '', formatLeft)
			worksheet.write(x, 29, employee_id.cts_bank_account_id.currency_id.name if employee_id.cts_bank_account_id.currency_id else '', formatLeft)
			worksheet.write(x, 30, employee_id.cts_bank_account_id.acc_number if employee_id.cts_bank_account_id.acc_number else '', formatLeft)
			worksheet.write(x, 31, last_contract.worker_type_id.name if last_contract.worker_type_id.name else '', formatLeft)
			worksheet.write(x, 32, last_contract.situation_id.name if last_contract.situation_id.name else '', formatLeft)
			worksheet.write(x, 33, dict(last_contract._fields['labor_regime'].selection).get(last_contract.labor_regime) if last_contract.labor_regime else '', formatLeft)
			worksheet.write(x, 34, employee_id.company_id.name if employee_id.company_id.name else '', formatLeft)
			worksheet.write(x, 35, employee_id.address if employee_id.address else '', formatLeft)
			worksheet.write(x, 36, employee_id.mobile_phone if employee_id.mobile_phone else '', formatLeft)

			x += 1

		widths = [19, 15, 15, 11, 12, 12,12, 12, 14, 20,21, 20, 18, 11, 16, 8, 14, 18, 14, 13, 16,
				  16, 14, 16,16, 18, 11, 18, 18, 11, 18, 13, 18, 15,18, 13, 13]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Reporte_historico_empleados.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte Historico Empleados.xlsx', base64.encodebytes(b''.join(f.readlines())))