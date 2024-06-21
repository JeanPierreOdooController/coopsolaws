# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from calendar import *

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'
	_order = 'employee_id'

	income = fields.Monetary(compute='_compute_basic_net', string='Ingresos')
	worker_contributions = fields.Monetary(compute='_compute_basic_net', string='Aportes Trabajador')
	net_discounts = fields.Monetary(compute='_compute_basic_net', string='Descuentos al Neto')
	net_to_pay = fields.Monetary(compute='_compute_basic_net', string='Neto a Pagar')
	employer_contributions = fields.Monetary(compute='_compute_basic_net', string='Aportes Empleador')
	holidays = fields.Integer(string='Dias Feriados y Domingos')

	identification_id = fields.Char(string="N° Identificacion")
	wage = fields.Monetary('Salario')
	labor_regime = fields.Selection([('general', 'Regimen General'),
									 ('small', 'Pequeña Empresa'),
									 ('micro', 'Micro Empresa'),
									 ('practice', 'Practicante'),
									 ('fourth-fifth', 'Trabajadores de 4ta-5ta')], string='Regimen Laboral')
	social_insurance_id = fields.Many2one('hr.social.insurance', string='Seguro Social')
	distribution_id = fields.Many2one('hr.analytic.distribution', string='Distribucion Analitica')
	workday_id = fields.Many2one('hr.workday', string='Jornada Laboral')

	membership_id = fields.Many2one('hr.membership', string='Afiliacion')
	commision_type = fields.Selection([('flow','Flujo'),('mixed','Mixta')],string='Tipo de Comision')
	fixed_commision = fields.Float(string='Comision Sobre Flujo %')
	mixed_commision = fields.Float(string='Comision Mixta %')
	prima_insurance = fields.Float(string='Prima de Seguros %')
	retirement_fund = fields.Float(string='Aporte Fondo de Pensiones %')
	insurable_remuneration = fields.Float(string='Remuneracion Asegurable')
	is_afp = fields.Boolean(string="is_afp")

	struct_type_id = fields.Many2one('hr.payroll.structure.type',string='Tipo de Planilla')
	partner_id = fields.Many2one('res.partner', string='Cliente')
	rmv = fields.Float('R.M.V.',default=1025)

	# payslip_run_consolidado_id = fields.Many2one('hr.resumen.planilla', string='Nombre del lote', readonly=True,
	# 	copy=False, states={'draft': [('readonly', False)], 'verify': [('readonly', False)]}, ondelete='cascade',
	# 	domain="[('company_id', '=', company_id)]")

	journal_id = fields.Many2one(related="")

	# @api.onchange('worked_days_line_ids','worked_days_line_ids.number_of_days')
	# def _get_number_of_days(self):
	# 	MainParameter = self.env['hr.main.parameter'].get_main_parameter()
	# 	MainParameter.check_voucher_values()
	# 	DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
	# 	DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
	# 	DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
	# 	WDLine = self.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
	# 	WD_DOM = self.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_dominical_wd)
	# 	WD_FER = self.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_feriado_wd)
	#
	# 	total = sum(DSUB.mapped('number_of_days')) + sum(DVAC.mapped('number_of_days')) + sum(DNLAB.mapped('number_of_days')) + WD_DOM.number_of_days + WD_FER.number_of_days
	# 	for record in self:
	# 		if record.struct_type_id.default_schedule_pay =='weekly':
	# 			dias_wd=7
	# 		elif record.struct_type_id.default_schedule_pay =='bi-weekly':
	# 			dias_wd=15
	# 		elif record.struct_type_id.default_schedule_pay =='monthly':
	# 			dias_wd=30
	# 		else:
	# 			dias_wd=(record.date_to-record.date_from).days+1
	#
	# 		if total == 0:
	# 			continue
	# 		else:
	# 			result = dias_wd - total
	# 			WDLine.number_of_days = result

	# @api.model
	# def create(self, vals):
	# 	rec = super(HrPayslip, self).create(vals)
	# 	rec.generate_inputs_and_wd_lines()
	# 	return rec

	def get_dlabs(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		#### WORKED DAYS ####
		DLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dlab.mapped('code'))
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))

		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))

		if sum(DLAB.mapped('number_of_days')) == 30:
			if DIA_SUB == 30:
				return 0
			elif DIA_VAC == 30:
				return 0
			elif (DIA_SUB + DIA_VAC) == 30:
				return 0
			else:
				return self.date_to.day - self.holidays - sum(DNLAB.mapped('number_of_days')) - DIA_SUB - DIA_VAC
		else:
			return sum(DLAB.mapped('number_of_days')) - self.holidays - sum(DNLAB.mapped('number_of_days')) - DIA_SUB - DIA_VAC

	def generate_inputs_and_wd_lines(self, recompute=False):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		for payslip in self:
			if recompute:
				input_type_lines = payslip.input_line_ids.mapped('input_type_id')
				wd_type_lines = payslip.worked_days_line_ids.mapped('wd_type_id')
			else:
				payslip.input_line_ids.unlink()
				payslip.worked_days_line_ids.unlink()
			input_types = payslip.struct_id.mapped('input_line_type_ids')
			wd_types = payslip.struct_id.mapped('wd_types_ids')
			for type in input_types:
				vals = {'input_type_id': type.id,
						'amount': 0,
						'payslip_id': payslip.id,
						'code': type.code,
						'contract_id': payslip.contract_id.id,
						'struct_id': payslip.struct_id.id}
				if recompute and type not in input_type_lines:
					self.env['hr.payslip.input'].create(vals)
				if not recompute:
					self.env['hr.payslip.input'].create(vals)
			for type in wd_types:
				if type.id == MainParameter.payslip_working_wd.id:
					if payslip.struct_type_id.default_schedule_pay =='weekly':
						dias_wd=7
					elif payslip.struct_type_id.default_schedule_pay =='bi-weekly':
						dias_wd=15
					elif payslip.struct_type_id.default_schedule_pay =='monthly':
						dias_wd=type.days
					else:
						dias_wd=(payslip.date_to-payslip.date_from).days+1
						# print("dias_wd",dias_wd)
				else:
					dias_wd=type.days
				vals = {'wd_type_id': type.id,
						'payslip_id': payslip.id,
						'number_of_days': dias_wd,
						'number_of_hours': type.hours}
				if recompute and type not in wd_type_lines:
					self.env['hr.payslip.worked_days'].create(vals)
				if not recompute:
					self.env['hr.payslip.worked_days'].create(vals)

	def compute_wds(self):
		for record in self:
			MainParameter = self.env['hr.main.parameter'].get_main_parameter()
			Holidays = self.env['hr.holidays'].search([('date', '>=', record.date_from),
													   ('date', '<=', record.date_to),
													   ('workday_id', '=', record.contract_id.workday_id.id)])
			record.holidays = len(Holidays)
			if not MainParameter.payslip_working_wd:
				raise UserError('Falta configurar un Worked Day para Dias Laborados en Parametros Principales de Nomina')
			if not MainParameter.payslip_dominical_wd:
				raise UserError('Falta configurar un Worked Day para el Dominical en Parametros Principales de Nomina')
			WD_DLAB = record.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
			WD_DOM = record.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_dominical_wd)
			Contract = self.env['hr.contract'].get_first_contract(record.employee_id, record.contract_id)

			if record.struct_type_id.default_schedule_pay =='weekly':
				dias_wd = 7
			elif record.struct_type_id.default_schedule_pay =='bi-weekly':
				if monthrange(record.date_from.year, record.date_from.month)[1] == record.date_to.day:
					dias_wd = record.date_to.day - 15
				else:
					dias_wd = 15
			elif record.struct_type_id.default_schedule_pay =='monthly':
				dias_wd = 30
			else:
				dias_wd=(record.date_to-record.date_from).days+1
			# print("dias_wd",dias_wd)

			WD_DAYS = record.worked_days_line_ids.filtered(lambda line: line.wd_type_id != MainParameter.payslip_working_wd)
			total_days = sum(WD_DAYS.mapped('number_of_days'))
			# print("total_days",total_days)

			if record.contract_id.structure_type_id.default_schedule_pay =='weekly':
				if Contract.date_start > record.date_from and Contract.date_start <= record.date_to:
					result = dias_wd - Contract.date_start.day + 1
					WD_DLAB.number_of_days = result-total_days
					WD_DOM.number_of_days = len(Holidays)
				else:
					# print("len(Holidays)",len(Holidays))
					WD_DLAB.number_of_days = (dias_wd-total_days) if WD_DOM.number_of_days > 0 else (dias_wd-len(Holidays)-total_days)
					WD_DOM.number_of_days = len(Holidays)
			else:
				if Contract.date_start > record.date_from and Contract.date_start <= record.date_to:
					result = dias_wd - Contract.date_start.day + 1
					WD_DLAB.number_of_days = result-total_days
				else:
					WD_DLAB.number_of_days = dias_wd-total_days

			if record.contract_id.situation_id.name == 'BAJA':
				if record.date_from <= record.contract_id.date_end <= record.date_to:
					if record.contract_id.date_start >= record.date_from:
						WD_DLAB.number_of_days = record.contract_id.date_end.day + 1 - record.contract_id.date_start.day - total_days
					elif record.date_from.month == record.contract_id.date_end.month:
						WD_DLAB.number_of_days = record.contract_id.date_end.day + 1 - record.date_from.day - total_days
					else:
						WD_DLAB.number_of_days = monthrange(record.date_from.year, record.date_from.month)[1] - record.date_from.day + record.contract_id.date_end.day - total_days

		return self.env['popup.it'].get_message('Se calculo correctamente')

	def _compute_basic_net(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		for payslip in self:
			payslip.basic_wage = 0
			payslip.income = payslip._get_salary_line_total(MainParameter.income_sr_id.code)
			payslip.worker_contributions = payslip._get_salary_line_total(MainParameter.worker_contributions_sr_id.code)
			payslip.net_wage = payslip._get_salary_line_total(MainParameter.net_sr_id.code)
			payslip.net_discounts = payslip._get_salary_line_total(MainParameter.net_discounts_sr_id.code)
			payslip.net_to_pay = payslip._get_salary_line_total(MainParameter.net_to_pay_sr_id.code)
			payslip.employer_contributions = payslip._get_salary_line_total(MainParameter.employer_contributions_sr_id.code)

	def action_payslip_hecho(self):
		return self.write({'state' : 'done'})

	def action_payslip_verify(self):
		return self.write({'state' : 'verify'})