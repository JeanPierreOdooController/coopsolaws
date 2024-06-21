# -*- coding:utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from math import modf

class HrPayslipRunConsolidado(models.Model):
	_name = 'hr.payslip.run.consolidado'
	_description = 'Hr Payslip Run Consolidado'
	_rec_name = 'periodo_id'
	_order = 'date_end desc'

	periodo_id = fields.Many2one('hr.period',string=u'Periodo',required=True, readonly=True, states={'draft': [('readonly', False)]})
	state = fields.Selection([
		('draft', 'Borrador'),
		('verify', 'En Proceso'),
		('close', 'Hecho'),
	], string='Estado', index=True, readonly=True, copy=False, default='draft')
	# slip_ids = fields.One2many('hr.payslip', 'payslip_run_consolidado_id', string='Payslips', states={'close': [('readonly', True)]})
	date_start = fields.Date(string='Desde', required=True, readonly=True, states={'draft': [('readonly', False)]})
	date_end = fields.Date(string='Hasta', required=True, readonly=True, states={'draft': [('readonly', False)]})
	# payslip_count = fields.Integer(compute='_compute_payslip_count')
	company_id = fields.Many2one('res.company', string=u'Compañia', readonly=True, required=True, default=lambda self: self.env.company)

	_sql_constraints = [
        ('uniq_planilla_consolidado', 'unique(period_id)', "Ya existe una planilla para este periodo. ¡El mes debe ser único!"),
    ]

	@api.onchange('periodo_id')
	def onchange_periodo(self):
		for rec in self:
			rec.date_start = rec.periodo_id.date_start
			rec.date_end = rec.periodo_id.date_end

	def _compute_payslip_count(self):
		for payslip_run in self:
			payslip_run.payslip_count = len(payslip_run.slip_ids)

	def set_draft(self):
		self.slip_ids.action_payslip_cancel()
		self.slip_ids.unlink()
		self.state = 'draft'

	def compute_wds_by_lot(self):
		self.slip_ids.compute_wds()

	def recompute_payslips(self):
		self.slip_ids.generate_inputs_and_wd_lines(True)
		self.slip_ids.compute_sheet()

	def close_payroll(self):
		self.state = 'close'
		self.slip_ids.action_payslip_hecho()

	def reopen_payroll(self):
		self.state = 'verify'
		self.slip_ids.action_payslip_verify()

	def action_open_payslips(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.payslip",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', 'in', self.slip_ids.ids]],
			"name": "Payslips",
		}

	def unlink(self):
		for record in self:
			if record.state != 'draft':
				raise UserError(_('¡No puede eliminar una planilla que no este en estado borrador!'))
		return super(HrPayslipRunConsolidado, self).unlink()

	def _are_payslips_ready(self):
		return all(slip.state in ['done', 'cancel'] for slip in self.mapped('slip_ids'))

	def get_consolidado(self):

		self.ensure_one()

		payslips = self.env['hr.payslip']
		Payslip = self.env['hr.payslip']

		structure_type_id = self.env['hr.payroll.structure.type'].search([('default_schedule_pay', '=', 'monthly')],limit=1).id
		struct_id = self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id

		self.env.cr.execute(self._get_sql_employee())
		res_employees = self.env.cr.dictfetchall()
		# print("res_employees",res_employees)

		default_values = Payslip.default_get(Payslip.fields_get())
		# print("self.structure_id",self.structure_id.name)
		for employee in res_employees:
			contract = self.env['hr.contract'].search([('id', '=', employee['contract_id']),('company_id', '=', self.env.company.id)],limit=1)
			values = dict(default_values, **{
				'name': 'Recibo Nomina - %s - %s' % (contract.employee_id.name or '',self.periodo_id.name or ''),
				'employee_id': contract.employee_id.id,
				'identification_id': contract.employee_id.identification_id,
				# 'credit_note': payslip_run.credit_note,
				'payslip_run_consolidado_id': self.id,
				'date_from': self.date_start,
				'date_to': self.date_end,
				'contract_id': contract.id,
				'struct_id': struct_id,
				'struct_type_id': structure_type_id,
				'wage': contract.wage,
				'labor_regime': contract.labor_regime,
				'social_insurance_id': contract.social_insurance_id.id,
				'distribution_id': contract.distribution_id.id,
				'workday_id': contract.workday_id.id,
				'membership_id': contract.membership_id.id,
				'commision_type': contract.commision_type,
				'fixed_commision': contract.membership_id.fixed_commision,
				'mixed_commision': contract.membership_id.mixed_commision,
				'prima_insurance': contract.membership_id.prima_insurance,
				'retirement_fund': contract.membership_id.retirement_fund,
				'insurable_remuneration': contract.membership_id.insurable_remuneration,
				'is_afp': contract.membership_id.is_afp,
				'holidays': employee['holidays'],
			})

			payslip = self.env['hr.payslip'].new(values)
			# payslip._onchange_employee()
			values = payslip._convert_to_write(payslip._cache)
			values['company_id']=self.env.company.id
			# print("values",values)
			payslips += Payslip.create(values)

		payslips.generate_inputs_and_wd_lines()
		# payslips.compute_sheet()

		# TRAENDO DATA DE PLANILLAS PEQUEÑAS
		for employee in res_employees:
			self.env.cr.execute(self._get_sql_wd(employee['employee_id']))
			res_wd = self.env.cr.dictfetchall()
			# print('res',res)
			for data in res_wd:
				# print('data',data)
				slip_wd = self.env['hr.payslip'].search([('payslip_run_consolidado_id', '=', self.id),
														 ('employee_id', '=', data['employee_id'])])
				# print('slip_wd',slip_wd)
				if len(slip_wd) == 0:
					raise UserError(u'El empleado seleccionado no existe en la nómina de ese periodo')
				for wd in slip_wd.worked_days_line_ids:
					# print('wd',wd)
					if wd.wd_type_id.id == data['wd_type_id']:
						# print("wd.wd_type_id.code",wd.wd_type_id.code)
						wd_line = wd
						# print('wd_line',wd_line)
						wd_line.number_of_days = data['wd_total_dias']
						wd_line.number_of_hours = data['wd_total_horas']

			self.env.cr.execute(self._get_sql_input(employee['employee_id']))
			res_input = self.env.cr.dictfetchall()
			# print('res',res)
			for data in res_input:
				# print('data',data)
				slip_input = self.env['hr.payslip'].search([('payslip_run_consolidado_id', '=', self.id),
															('employee_id', '=', data['employee_id'])])
				# print('slip_input',slip_input)
				if len(slip_input) == 0:
					raise UserError(u'El empleado seleccionado no existe en la nómina de ese periodo')
				for input in slip_input.input_line_ids:
					# print('wd',wd)
					if input.input_type_id.id == data['input_type_id']:
						# print("input.input_type_id.code",input.input_type_id.code)
						input_line = input
						# print('input_line',input_line)
						input_line.amount = data['total_amount']

		self.slip_ids.generate_inputs_and_wd_lines(True)
		self.slip_ids.compute_sheet()
		self.state = 'verify'

		return {
			'effect': {
				'fadeout': 'slow',
				'message': "Generacion exitosa",
				'type': 'rainbow_man',
			}
		}

	def _get_sql_employee(self):
		sql = """
            select
			he.id as employee_id,
			he.identification_id,
			he.name,
			max(hp.contract_id) as contract_id,
			sum(hp.holidays) as holidays
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id
			where 
			hp.company_id = %d
			and extract(month from hp.date_to) = %d
			and extract(year from hp.date_to) = %d
			and hp.payslip_run_id is not null
			group by he.id,he.identification_id,he.name
			order by he.identification_id
			"""%(self.company_id.id,int(self.date_start.month),
				 int(self.periodo_id.fiscal_year_id.name))
		# print("sql",sql)
		return sql

	def _get_sql_input(self,employee):
		sql = """
            select
			he.id as employee_id,
			he.identification_id,
			he.name,
--			hc.id as contract_id,
			hpit.code as input_code,
			hpit.id as input_type_id,
			sum(hpi.amount) as total_amount
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id 
--			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_payslip_input hpi on hpi.payslip_id=hp.id
			left join hr_payslip_input_type hpit on hpit.id=hpi.input_type_id
			where 
			hp.company_id = %d
			and extract(month from hp.date_to) = %d
			and extract(year from hp.date_to) = %d
			and hpi.amount <> 0
			and he.id = %d
			and hp.payslip_run_id is not null
			group by he.id,he.identification_id,he.name,hpit.code,hpit.id
			order by he.identification_id
			"""%(self.company_id.id,int(self.date_start.month),
				 int(self.periodo_id.fiscal_year_id.name), int(employee))
		return sql

	def _get_sql_wd(self,employee):
		sql = """
			select
			he.id as employee_id,
			he.identification_id,
			he.name,
--			hc.id as contract_id,
			hpwdt.code as code,
			hpwdt.id as wd_type_id,
			sum(hpwd.number_of_days) as wd_total_dias,
			sum(hpwd.number_of_hours) as wd_total_horas
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id 
--			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_payslip_worked_days hpwd on hpwd.payslip_id=hp.id
			left join hr_payslip_worked_days_type hpwdt on hpwdt.id=hpwd.wd_type_id
			where 
			hp.company_id = %d
			and extract(month from hp.date_to) = %d
			and extract(year from hp.date_to) = %d
			and(hpwd.number_of_days <> 0 or hpwd.number_of_hours <> 0)
			and he.id = %d
			and hp.payslip_run_id is not null
			group by he.id,he.identification_id,he.name,hpwdt.code,hpwdt.id
			order by he.identification_id
			""" %(self.company_id.id,int(self.date_start.month),
				  int(self.periodo_id.fiscal_year_id.name), int(employee))
		return sql

	def tab_payroll(self):
		return {
			'name': 'Planilla Tabular',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'hr.planilla.tabular.salary.consolidado.wizard',
			'context': {'default_payslip_run_consolidado_id': self.id},
			'target': 'new',
		}

	def afp_net(self):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file
		insurable_remuneration = MainParameter.insurable_remuneration
		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'AFP_NET.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("AFP NET")
		worksheet.set_tab_color('blue')
		x = 0
		for c, slip in enumerate(self.slip_ids):
			if slip.contract_id.membership_id.is_afp:
				Contract = slip.contract_id
				Employee = slip.contract_id.employee_id
				FirstContract = self.env['hr.contract'].get_first_contract(Employee, Contract)
				ir_line = self.env['hr.payslip.line'].search([('salary_rule_id', '=', insurable_remuneration.id),('slip_id', '=', slip.id)])
				worksheet.write(x, 0, c)
				worksheet.write(x, 1, Contract.cuspp if Contract.cuspp else '')
				worksheet.write(x, 2, Employee.type_document_id.afp_code if Employee.type_document_id.afp_code else '')
				worksheet.write(x, 3, Employee.identification_id if Employee.identification_id else '')
				worksheet.write(x, 4, Employee.last_name if Employee.last_name else '')
				worksheet.write(x, 5, Employee.m_last_name if Employee.m_last_name else '')
				worksheet.write(x, 6, Employee.names if Employee.names else '')
				worksheet.write(x, 7, 'N' if Contract.situation_id.code == '0' else 'S')
				worksheet.write(x, 8, 'S' if FirstContract.date_start >= self.date_start and FirstContract.date_start <= self.date_end else 'N')
				worksheet.write(x, 9, 'S' if FirstContract.date_end and FirstContract.date_end >= self.date_start and FirstContract.date_end <= self.date_end else 'N')
				worksheet.write(x, 10, Contract.exception if Contract.exception else '')
				worksheet.write(x, 11, ir_line.total if ir_line.total else 0.00, formats['numberdosespecial'])
				worksheet.write(x, 12, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 13, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 14, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 15, Contract.work_type if Contract.work_type else 'N')
				x += 1

		widths = [2, 15, 2, 12, 20, 20, 20, 2, 2, 2, 2, 8, 8, 8, 8, 2]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'AFP_NET.xlsx', 'rb')
		return self.env['popup.it'].get_file('AFP_NET.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def export_plame(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.rem' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					sql = """
						select min(a1.doc_type) as doc_type,
                            a1.dni,
                            a1.sunat,
                            sum(a1.amount_earn) as amount_earn,
                            sum(a1.amount_paid) as amount_paid
                        from (
                        select
						htd.sunat_code as doc_type,
						he.identification_id as dni,
						sr.sunat_code as sunat,
						hpl.total as amount_earn,
						hpl.total as amount_paid
						from hr_payslip_run_consolidado hpr
						inner join hr_payslip hp on hpr.id = hp.payslip_run_consolidado_id
						inner join hr_payslip_line hpl on hp.id = hpl.slip_id
						inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
						inner join hr_employee he on he.id = hpl.employee_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id =  %d
						and he.id =  %d
						and sr.sunat_code != ''
						and sr.sunat_code not in ('0804','0607','0605','0601')
						and hpl.total != 0
                        union all 
                        select
						htd.sunat_code as doc_type,
						he.identification_id as dni,
						sr.sunat_code as sunat,
						hpl.total as amount_earn,
						hpl.total as amount_paid
						from hr_payslip_run_consolidado hpr
						inner join hr_payslip hp on hpr.id = hp.payslip_run_consolidado_id
						inner join hr_payslip_line hpl on hp.id = hpl.slip_id
						inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
						inner join hr_employee he on he.id = hpl.employee_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id =  %d
						and he.id =  %d
						and sr.sunat_code in ('0605','0601')) a1
					    group by a1.sunat, a1.dni
						order by a1.sunat 
						""" % (self.env.company.id,payslip_run.id, payslip.employee_id.id,
							   self.env.company.id,payslip_run.id, payslip.employee_id.id)
					self._cr.execute(sql)
					data = self._cr.dictfetchall()
					for line in data:
						f.write("%s|%s|%s|%s|%s|\r\n" % (
							line['doc_type'],
							line['dni'],
							line['sunat'],
							line['amount_earn'],
							line['amount_paid']
						))
				employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.rem' % (first, second, self.company_id.vat),base64.encodestring(b''.join(f.readlines())))

	def export_plame_hours(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.jor' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					sql = """
						select
						min(htd.sunat_code) as doc_type,
						he.identification_id as dni,
						sum(case when hpwd.wd_type_id in ({fal}) then hpwd.number_of_days else 0 end) as fal,
						sum(case when hpwd.wd_type_id in ({hext}) then hpwd.number_of_hours else 0 end) as hext,
						sum(case when hpwd.wd_type_id in ({dvac}) then hpwd.number_of_days else 0 end) as dvac,
						min(rc.hours_per_day) as hours_per_day
						from hr_payslip hp
						inner join hr_employee he on he.id = hp.employee_id
						inner join hr_contract hc on hc.id = hp.contract_id
						inner join resource_calendar rc on rc.id = hc.resource_calendar_id
						inner join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
						inner join hr_payslip_worked_days_type hpwdt on hpwdt.id = hpwd.wd_type_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where hp.payslip_run_consolidado_id = {pr_id}
						and hp.employee_id = {emp_id}
						and hpwd.wd_type_id in ({fal},{hext},{dvac})
						group by htd.sunat_code, he.identification_id
						""".format(
						pr_id = payslip_run.id,
						emp_id = payslip.employee_id.id,
						fal = ','.join(str(id) for id in MainParameter.wd_dnlab.ids),
						hext = ','.join(str(id) for id in MainParameter.wd_ext.ids),
						dvac = ','.join(str(id) for id in MainParameter.wd_dvac.ids)
					)
					self._cr.execute(sql)
					data = self._cr.dictfetchall()
					for line in data:
						dlab = payslip.get_dlabs()
						hlab = modf(dlab * line['hours_per_day'])
						f.write("%s|%s|%d|0|%d|0|\r\n" % (
							line['doc_type'],
							line['dni'],
							hlab[1],
							line['hext']
						))
				employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.jor' % (first, second, self.company_id.vat),base64.encodestring(b''.join(f.readlines())))