# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from datetime import *
from math import modf
from string import ascii_lowercase
import itertools

class HrPlanillaTabularSalaryWizard(models.TransientModel):
	_inherit = 'hr.planilla.tabular.salary.wizard'

	def _get_tab_payroll_sql(self,option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""
		struct_id = self.payslip_run_id.slip_ids[0].struct_id.id
		sql = """
			select
			he.id as employee_id,
			he.identification_id,
			(he.identification_id::text ||he.id::text|| hc.id::text) AS code_unico,
			hc.date_start,
			hc.date_end,
			hm.name as membership,
			had.name as distribution,
			hsr.code,
			hsr.name as name_salary,
			sum(hpl.total)
			from hr_payslip hp
			inner join hr_payslip_line hpl on hpl.slip_id = hp.id
			inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
			inner join hr_employee he on he.id = hp.employee_id
			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_membership hm on hm.id = hc.membership_id
			left join hr_analytic_distribution had on had.id = hc.distribution_id
			where hp.id in ({ids})
			and hsr.appears_on_payslip = true
			and hsr.active = true
			and hsr.company_id = {company}
			and hsr.struct_id = {struct_id}
			{sql_employees}
			group by he.identification_id, he.id, hc.id, hc.date_start, hc.date_end, hsr.code, hsr.name, hm.name, had.name, hsr.sequence
			order by he.identification_id,(he.identification_id::text ||he.id::text|| hc.id::text), hsr.sequence
		""".format(
				ids = ','.join(list(map(str, self.payslip_run_id.slip_ids.ids))),
				company = self.company_id.id,
				struct_id = struct_id,
				sql_employees = sql_employees
			)
		return sql

	def _get_sql_wd(self,code_unico):
		struct_id = self.payslip_run_id.slip_ids[0].struct_id.id
		sql = """
		select      
			T.employee_id,
			T.identification_id,
			(T.identification_id::text ||T.employee_id::text|| T.contract_id::text) AS code_unico,
			T.name,
			T.contract_id,
			sum(T.dlab) AS dlab,
			sum(T.hdlab) AS hdlab,
			sum(T.dlabn) AS dlabn,
			sum(T.hdlabn) AS hdlabn,
			sum(T.dom) AS dom,
			sum(T.hdom) AS hdom,
			sum(T.dfer) AS dfer,
			sum(T.dfal) AS dfal,
			sum(T.htar) AS htar,
			sum(T.dmed) AS dmed,
			sum(T.dvac) AS dvac,
			sum(T.dsub) AS dsub,
			sum(T.he25) AS he25,
			sum(T.he35) AS he35,
			sum(T.he50) AS he50,
			sum(T.he100) AS he100
			FROM 
				(
				select      
				T.employee_id,
				T.identification_id,
				T.name,
				T.contract_id,
				case when T.code in ('DLAB') then sum(T.wd_total_dias) else 0 end  as dlab,
				case when T.code in ('DLAB') then sum(T.wd_total_horas) else 0 end  as hdlab,
				case when T.code in ('DLABN') then sum(T.wd_total_dias) else 0 end  as dlabn,
				case when T.code in ('DLABN') then sum(T.wd_total_horas) else 0 end  as hdlabn,
				case when T.code in ('DOM') then sum(T.wd_total_dias) else 0 end  as dom,
				case when T.code in ('DOM') then sum(T.wd_total_horas) else 0 end  as hdom,
				case when T.code in ('FER') then sum(T.wd_total_dias) else 0 end  as dfer,
				case when T.code in ('FAL') then sum(T.wd_total_dias) else 0 end  as dfal,
				case when T.code in ('TAR') then sum(T.wd_total_horas) else 0 end  as htar,
				case when T.code in ('DMED') then sum(T.wd_total_dias) else 0 end  as dmed,
				case when T.code in ('DVAC') then sum(T.wd_total_dias) else 0 end  as dvac,
				case when T.code in ('SMAR','SENF') then sum(T.wd_total_dias) else 0 end  as dsub,
				case when T.code in ('HE25') then sum(T.wd_total_horas) else 0 end  as he25,
				case when T.code in ('HE35') then sum(T.wd_total_horas) else 0 end  as he35,
				case when T.code in ('HE50') then sum(T.wd_total_horas) else 0 end  as he50,
				case when T.code in ('HE100') then sum(T.wd_total_horas) else 0 end  as he100
				from (		SELECT	
							he.id as employee_id,
							he.identification_id,
							he.name,
							hc.id as contract_id,
							hpwdt.code as code,
							hpwdt.id as wd_type_id,
							sum(hpwd.number_of_days) as wd_total_dias,
							sum(hpwd.number_of_hours) as wd_total_horas
							from hr_payslip hp 
							inner join hr_employee he on he.id = hp.employee_id 
							inner join hr_contract hc on hc.id = hp.contract_id
							left join hr_payslip_worked_days hpwd on hpwd.payslip_id=hp.id
							left join hr_payslip_worked_days_type hpwdt on hpwdt.id=hpwd.wd_type_id
							where hp.id in ({ids})
							and hp.company_id = {company}
							and hp.struct_id = {struct_id}
--							and(hpwd.number_of_days <> 0 or hpwd.number_of_hours <> 0)
							group by he.id,he.identification_id,hc.id,hpwdt.code,hpwdt.id
							order by he.identification_id
				)T
				group by T.employee_id,	T.identification_id, T.name, T.contract_id,	T.code,	T.wd_type_id
				order by T.identification_id
			)T
			where (T.identification_id::text ||T.employee_id::text|| T.contract_id::text) = '{code_unico}'
			group by T.employee_id,	T.identification_id, T.name, T.contract_id
			""" .format(
				ids = ','.join(list(map(str, self.payslip_run_id.slip_ids.ids))),
				company = self.company_id.id,
				struct_id = struct_id,
				code_unico = code_unico
			)
		return sql

	def get_excel(self, option):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Planilla_Tabular.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Planilla Tabular")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])
		worksheet.merge_range(4, 1, 4, 8, "*** PLANILLA DE SUELDOS Y SALARIOS %s ***" % self.payslip_run_id.name or '', formats['especial5'])

		self._cr.execute(self._get_tab_payroll_sql(option))
		data = self._cr.dictfetchall()

		x, y = 7, 23
		limit = len(data[0] if data else 0)
		# struct_id = self.payslip_run_id.slip_ids[0].struct_id.id
		# SalaryRules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True), ('struct_id', '=', struct_id)], order='sequence')
		# names = SalaryRules.mapped('name')
		# codes = SalaryRules.mapped('code')
		names = []
		codes = []
		for elem in data:
			if elem['code'] in codes:
				continue
			else:
				names.append(elem['name_salary'])
				codes.append(elem['code'])
		size = len(codes)

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

		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)

		worksheet.merge_range(5, 7, 5, 22, "TAREAJE WORKED DAYS", boldbord)
		worksheet.merge_range(6, 7, 6, 8, "Dias Laborados Diurnos", boldbord)
		worksheet.merge_range(6, 9, 6, 10, "Dias Laborados Nocturnos", boldbord)
		worksheet.merge_range(6, 11, 6, 12, "Dominical", boldbord)
		worksheet.write(x, 0, 'N° de Identificacion', boldbord)
		worksheet.write(x, 1, 'Apellidos y Nombres', boldbord)
		worksheet.write(x, 2, 'Puesto de Trabajo', boldbord)
		worksheet.write(x, 3, 'Afiliacion', boldbord)
		worksheet.write(x, 4, 'Distribucion Analitica', boldbord)
		worksheet.write(x, 5, 'Fecha de Ingreso', boldbord)
		worksheet.write(x, 6, 'Fecha de Cese', boldbord)
		worksheet.write(x, 7, 'Dias', boldbord)
		worksheet.write(x, 8, 'Horas', boldbord)
		worksheet.write(x, 9, 'Dias', boldbord)
		worksheet.write(x, 10, 'Horas', boldbord)
		worksheet.write(x, 11, 'Dias', boldbord)
		worksheet.write(x, 12, 'Horas', boldbord)
		worksheet.merge_range(x-1, 13, x, 13, "Dias Feriados", boldbord)
		worksheet.merge_range(x-1, 14, x, 14, 'Dias Faltas', boldbord)
		worksheet.merge_range(x-1, 15, x, 15, 'Horas Tardanzas', boldbord)
		worksheet.merge_range(x-1, 16, x, 16, 'Dias Descanso Medico', boldbord)
		worksheet.merge_range(x-1, 17, x, 17, 'Dias Vacaciones', boldbord)
		worksheet.merge_range(x-1, 18, x, 18, 'Dias Subsidiados', boldbord)
		worksheet.merge_range(x-1, 19, x, 19, 'Horas Extras 25%', boldbord)
		worksheet.merge_range(x-1, 20, x, 20, 'Horas Extras 35%', boldbord)
		worksheet.merge_range(x-1, 21, x, 21, 'Horas Extras 50%', boldbord)
		worksheet.merge_range(x-1, 22, x, 22, 'Horas Extras 100%', boldbord)

		for name in names:
			worksheet.write(x, y, name, boldbord)
			y += 1
		x += 1
		table = []
		row = []
		aux_id, limit = '', len(data)
		for c, line in enumerate(data, 1):
			# print("line",line)
			if aux_id != line['code_unico']:
				if len(row) > 0:
					table.append(row)
					x += 1
				row = []
				employee = self.env['hr.employee'].browse(line['employee_id'])
				self.env.cr.execute(self._get_sql_wd(line['code_unico']))
				res_wds = self.env.cr.dictfetchall()
				# print("res_wds",res_wds)
				for emplo_wd in res_wds:
					worksheet.write(x, 0, line['identification_id'] if line['identification_id'] else '', formatLeft)
					worksheet.write(x, 1, employee.name if employee.name else '', formatLeft)
					worksheet.write(x, 2, employee.job_title if employee.job_title else '', formatLeft)
					worksheet.write(x, 3, line['membership'] if line['membership'] else '', formatLeft)
					worksheet.write(x, 4, line['distribution'] if line['distribution'] else '', formatLeft)
					worksheet.write(x, 5, line['date_start'] if line['date_start'] else '', dateformat)
					worksheet.write(x, 6, line['date_end'] if line['date_end'] else '', dateformat)
					worksheet.write(x, 7, emplo_wd['dlab'] if emplo_wd['dlab'] else 0.0, numberdos)
					worksheet.write(x, 8, emplo_wd['hdlab'] if emplo_wd['hdlab'] else 0.0, numberdos)
					worksheet.write(x, 9, emplo_wd['dlabn'] if emplo_wd['dlabn'] else 0.0, numberdos)
					worksheet.write(x, 10, emplo_wd['hdlabn'] if emplo_wd['hdlabn'] else 0.0, numberdos)
					worksheet.write(x, 11, emplo_wd['dom'] if emplo_wd['dom'] else 0.0, numberdos)
					worksheet.write(x, 12, emplo_wd['hdom'] if emplo_wd['hdom'] else 0.0, numberdos)
					worksheet.write(x, 13, emplo_wd['dfer'] if emplo_wd['dfer'] else 0.0, numberdos)
					worksheet.write(x, 14, emplo_wd['dfal'] if emplo_wd['dfal'] else 0.0, numberdos)
					worksheet.write(x, 15, emplo_wd['htar'] if emplo_wd['htar'] else 0.0, numberdos)
					worksheet.write(x, 16, emplo_wd['dmed'] if emplo_wd['dmed'] else 0.0, numberdos)
					worksheet.write(x, 17, emplo_wd['dvac'] if emplo_wd['dvac'] else 0.0, numberdos)
					worksheet.write(x, 18, emplo_wd['dsub'] if emplo_wd['dsub'] else 0.0, numberdos)
					worksheet.write(x, 19, emplo_wd['he25'] if emplo_wd['he25'] else 0.0, numberdos)
					worksheet.write(x, 20, emplo_wd['he35'] if emplo_wd['he35'] else 0.0, numberdos)
					worksheet.write(x, 21, emplo_wd['he50'] if emplo_wd['he50'] else 0.0, numberdos)
					worksheet.write(x, 22, emplo_wd['he100'] if emplo_wd['he100'] else 0.0, numberdos)

					worksheet.write(x, 23, line['sum'] if line['sum'] else 0.0, numberdos)
					row.append(line['sum'])
					y = 23
					aux_id = line['code_unico']
			else:
				y += 1
				worksheet.write(x, y, line['sum'] if line['sum'] else 0.0, numberdos)
				aux_id = line['code_unico']
				row.append(line['sum'])
				if c == limit:
					table.append(row)
					x += 1

		zipped_table = zip(*table)
		y = 23
		for row in zipped_table:
			worksheet.write(x, y, sum(list(row)), styleFooterSum)
			y += 1
		widths = [15, 40, 22, 16, 15, 12, 12, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10] + size * [16]
		worksheet = self.resize_cells(worksheet, widths)
		workbook.close()
		f = open(directory + 'Planilla_Tabular.xlsx', 'rb')
		return self.env['popup.it'].get_file('Planilla %s.xlsx' % self.payslip_run_id.name, base64.encodebytes(b''.join(f.readlines())))