# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from collections import namedtuple

class hr_work_suspension(models.Model):
	_inherit='hr.work.suspension'

	leave_id = fields.Many2one('hr.leave','Ausencia')

class hr_accrual_vacation(models.Model):
	_inherit='hr.accrual.vacation'

	leave_id = fields.Many2one('hr.leave','Ausencia')

class HrLeaveAllocation(models.Model):
	_inherit = 'hr.leave.allocation'

	payslip_run_id = fields.Many2one('hr.payslip.run','Periodo')
	contract_id = fields.Many2one('hr.contract','Contrato')
	comment_to_eployee = fields.Text('Nota para el empleado')
	comment_from_eployee = fields.Text('Comentario del empleado')
	leave_type_id = fields.Many2one('hr.leave.type.it','Tipo de ausencia')

	leave_motive_id = fields.Many2one('hr.leave.motive.it',u'Modo de Asignación')	

class HrLeaveType(models.Model):
	_inherit = 'hr.leave.type'

	suspension_type_id = fields.Many2one('hr.suspension.type',u'Tipo de Suspensión')
	ausencia_wd_id = fields.Many2one('hr.payslip.worked_days.type', string='WD Ausencia')

class HrLeave(models.Model):
	_inherit = 'hr.leave'

	contract_id = fields.Many2one('hr.contract','Contrato')
	leave_type_id = fields.Many2one('hr.leave.type.it','Tipo de Ausencia')
	payslip_run_id = fields.Many2one('hr.payslip.run','Planilla')
	leave_motive_id = fields.Many2one('hr.leave.motive.it',u'Modo de Asignación')
	# comment_to_eployee = fields.Text('Nota para el empleado')
	# comment_from_eployee = fields.Text('Comentario del empleado')
	work_suspension_id = fields.Many2one('hr.suspension.type',related='holiday_status_id.suspension_type_id', string=u'Tipo de Suspensión', store=True)
	validation_type = fields.Selection('Tipo de Validacion', related='holiday_status_id.validation_type', readonly=False)

	employee_id = fields.Many2one(
		'hr.employee', string='Empleado', index=True,  ondelete="restrict",
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, tracking=True)
	
	department_id = fields.Many2one(
		'hr.department', string='Departamento', readonly=True,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

	# @api.onchange('payslip_run_id')
	# def onchange_holiday(self):
	# 	parameters = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
	# 	for res in self:
	# 		res.work_suspension_id = parameters.suspension_type_id

	# @api.depends('payslip_run_id')
	# def get_parameter(self):
	# 	parameters = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
	# 	print(parameters)
	# 	for res in self:
	# 		res.work_suspension_id = parameters.suspension_type_id

	def _get_number_of_days(self, date_from, date_to, employee_id):
		if employee_id:
			employee = self.env['hr.employee'].browse(employee_id)
			return {'days': (date_to-date_from).days+1, 'hours': 0}
		return {'days': (date_to-date_from).days+1, 'hours': 0}


	@api.model
	def default_get(self, fields_list):
		defaults = super(HrLeave, self).default_get(fields_list)
		defaults = self._default_get_request_parameters(defaults)
		suspension_type_id = self.env['hr.suspension.type'].search([('code', '=','23')], limit=1)
		LeaveType = self.env['hr.leave.type'].search([('active', '=', True),('suspension_type_id', '=', suspension_type_id.id)], limit=1)
		# print("LeaveType",LeaveType.name)
		defaults['holiday_status_id'] = LeaveType.id if LeaveType else defaults.get('holiday_status_id')
		# defaults['work_suspension_id'] = parameters.suspension_type_id.id
		return defaults

	@api.onchange('contract_id')
	def onchange_contract(self):
		if self.contract_id.id:
			self.employee_id = self.contract_id.employee_id.id
			self.department_id = self.contract_id.employee_id.department_id.id
		else:
			self.employee_id=None
			self.department_id = None

	def action_confirm(self):
		for rec in self:
			if rec.filtered(lambda holiday: holiday.state != 'draft'):
				raise UserError(_('La solicitud de Ausencia debe estar en estado Borrador, para poder confirmarla.'))
			rec.write({'state': 'confirm'})
			holidays = rec.filtered(lambda leave: leave.validation_type == 'no_validation')
			if holidays:
				# La validación automática debe realizarse en sudo, ya que es posible que el usuario no tenga los derechos para hacerlo por sí mismo.
				holidays.sudo().action_validate()
			rec.activity_update()
		return True

	def action_refuse(self):
		l = self.contract_id.work_suspension_ids.filtered(lambda reg: reg.leave_id.id == self.id)
		h = self.env['hr.accrual.vacation'].search([('leave_id','=',self.id)])
		# print("l",l)
		# print("l",h)
		if self.payslip_status or len(l)>0 or len(h)>0:
			# raise UserError(u'No se puede rechazar si ya se encuentra en reportado en planilla')
			self.payslip_status = False
			if self.holiday_status_id.ausencia_wd_id:
				slip = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip_run_id.id),('employee_id','=',self.employee_id.id)])
				wd_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == self.holiday_status_id.ausencia_wd_id)
				wd_line.number_of_days = wd_line.number_of_days - self.number_of_days
				slip.compute_wds()
			l.unlink()
			h.unlink()
		super(HrLeave,self).action_refuse()

	# def action_approve(self):
	# 	if self.holiday_status_id.validation_type == 'no_validation':
	# 		return super(HrLeave,self).action_approve()
	# 	else:
	# 		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
	# 		valida1 = False
	# 		valida2 = False
	# 		first_validators=[]
	# 		second_validators=[]
	# 		res=False
	# 		for l in MainParameter.validator_ids:
	# 			if self.env.user.id == l.user_id.id:
	# 				if l.first_validate:
	# 					valida1=l.first_validate
	# 				if l.second_validate:
	# 					valida2=l.second_validate
	# 			if l.first_validate:
	# 				first_validators.append(l.user_id.id)
	# 			if l.second_validate:
	# 				second_validators.append(l.user_id.id)
	#
	#
	# 		if not valida1:
	# 			raise UserError(u'No tiene permiso para realizar esta operación')
	# 		else:
	# 			if self.env.user.id in first_validators:
	# 				res = super(HrLeave,self).action_approve()
	# 			else:
	# 				raise UserError(u'No tiene permiso para realizar esta operación')
	# 		return res


	def action_validate(self):
		if self.holiday_status_id.validation_type == 'no_validation':
			return super(HrLeave,self).action_validate()
		else:
			MainParameter = self.env['hr.main.parameter'].get_main_parameter()
			valida1 = False
			valida2 = False
			first_validators=[]
			second_validators=[]
			res=False
			for l in MainParameter.validator_ids:
				if self.env.user.id == l.user_id.id:
					if l.first_validate:
						valida1=l.first_validate
					if l.second_validate:
						valida2=l.second_validate
				if l.first_validate:
					first_validators.append(l.user_id.id)
				if l.second_validate:
					second_validators.append(l.user_id.id)
			if not valida2:
				raise UserError(u'No tiene permiso para realizar esta operación')
			else:
				if self.env.user.id in second_validators:

					res = super(HrLeave,self).action_validate()

				else:
					raise UserError(u'No tiene permiso para realizar esta operación')
			return res

	def prepare_suspension_data(self, contract_id):
		vals = {}
		if self.work_suspension_id:
			periodo_id = self.env['hr.period'].search([('date_start','<=',self.request_date_from),('date_end','>=',self.request_date_from)],limit=1)
			vals = {
				'suspension_type_id': self.work_suspension_id.id,
				'reason': self.holiday_status_id.ausencia_wd_id.name,
				'days': self.number_of_days,
				'payslip_run_id': self.payslip_run_id.id,
				'periodo_id': periodo_id.id,
				'leave_id': self.id,
				'contract_id': contract_id.id,
			}
		return vals

	def prepare_payslip_data(self, slip):
		vals = {
			'days': self.number_of_days,
			'accrued_period': self.payslip_run_id.id,
			'motive':self.holiday_status_id.name,
			'date_aplication':self.request_date_from,
			'request_date_from': self.request_date_from,
			'request_date_to': self.request_date_to,
			'leave_id': self.id,
			'slip_id': slip.id,
		}
		return vals

	def send_data_to_payslip(self):
		# MainParameter = self.env['hr.main.parameter'].get_main_parameter()

		for l in self:
			if not l.payslip_run_id:
				raise UserError(
					u'La ausencia %s de %s no tiene asignada una planilla Mensual' % (l.name, l.employee_id.name))
			if l.payslip_status == False:
				if l.state == 'validate':
					slip = self.env['hr.payslip'].search([('payslip_run_id', '=', l.payslip_run_id.id), ('employee_id', '=', l.employee_id.id)])
					if len(slip) == 0:
						raise UserError(u'El empleado %s no existe en la Planilla de %s' % (
						l.employee_id.name, l.payslip_run_id.name.name))
					if l.work_suspension_id:
						vals = l.prepare_suspension_data(slip.contract_id)
						# print("vals",vals)
						self.env['hr.work.suspension'].create(vals)

					if l.work_suspension_id.code == '23':
						vals = l.prepare_payslip_data(slip)
						# print(vals)
						self.env['hr.accrual.vacation'].create(vals)

					wd_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == l.holiday_status_id.ausencia_wd_id)
					if l.holiday_status_id.ausencia_wd_id:
						wd_line.number_of_days = wd_line.number_of_days + l.number_of_days

					# DIAS_FAL = slip.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code')).mapped('code')
					# dia_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
					# wd_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == l.leave_type_id.ausencia_wd_id)
					# if wd_line.code in tuple(DIAS_FAL):
					#     wd_line.number_of_days = wd_line.number_of_days + l.number_of_days
					# else:
					#     wd_line.number_of_days = wd_line.number_of_days + l.number_of_days
					# dia_line.number_of_days = 30 - l.number_of_days
					l.payslip_status = True
					slip.compute_wds()
				else:
					raise UserError(
						u'Para reportar a la planilla, primero debe de confirmar esta ausencia: %s de %s.' % (l.name, l.employee_id.name))
			else:
				raise UserError(u'La ausencia %s de %s ya fue enviada a la planilla Mensual' % (l.name, l.employee_id.name))
		return self.env['popup.it'].get_message(u'Se mandó al Lote de Nóminas exitosamente.')


	@api.model_create_multi
	def create(self, vals_list):
		for l in vals_list:
			# print(l)
			c = self.env['hr.contract'].browse(l['contract_id'])
			l['employee_id']=c.employee_id.id

		holidays = super(HrLeave, self.with_context(mail_create_nosubscribe=True,leave_fast_create=True)).create(vals_list)
		return holidays

	@api.constrains('state', 'number_of_days', 'holiday_status_id')
	def _check_holidays(self):
		mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
		for holiday in self:
			continue
	
	def _sync_employee_details(self):
		for holiday in self:
			holiday.manager_id = holiday.employee_id.parent_id.id
			if holiday.employee_id:
				holiday.department_id = holiday.employee_id.department_id


	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		self._sync_employee_details()

class HrLeaveTypeIt(models.Model):
	_name = 'hr.leave.type.it'
	_description = u'Tipo de Ausencia'

	name=fields.Char('Tipo de Ausencia')
	is_vacation=fields.Boolean('Vacaciones')


class HrLeaveMotiveIt(models.Model):
	_name = 'hr.leave.motive.it'
	_description = u'Motivo de Asignación'

	name = fields.Char(u'Motivo de Asignación')



class LeaveReport(models.Model):
	_inherit = "hr.leave.report"	

	work_suspension_id = fields.Many2one('hr.suspension.type', u'Tipo de Suspensión')

	def init(self):
		tools.drop_view_if_exists(self._cr, 'hr_leave_report')

		self._cr.execute("""
			CREATE or REPLACE view hr_leave_report as (
				SELECT row_number() over(ORDER BY leaves.employee_id) as id,
				leaves.employee_id as employee_id, leaves.name as name,
				leaves.number_of_days as number_of_days, leaves.leave_type as leave_type,
				leaves.category_id as category_id, leaves.department_id as department_id,
				leaves.holiday_status_id as holiday_status_id, leaves.state as state,
				leaves.holiday_type as holiday_type, leaves.date_from as date_from,
				leaves.date_to as date_to, leaves.payslip_status as payslip_status,
				leaves.work_suspension_id as work_suspension_id
				from (select
					allocation.employee_id as employee_id,
					allocation.name as name,
					allocation.number_of_days as number_of_days,
					allocation.category_id as category_id,
					allocation.department_id as department_id,
					allocation.holiday_status_id as holiday_status_id,
					allocation.state as state,
					allocation.holiday_type,
					null as date_from,
					null as date_to,
					FALSE as payslip_status,
					'allocation' as leave_type,
					null as work_suspension_id
				from hr_leave_allocation as allocation
				union all select
					request.employee_id as employee_id,
					request.name as name,
					(request.number_of_days * -1) as number_of_days,
					request.category_id as category_id,
					request.department_id as department_id,
					request.holiday_status_id as holiday_status_id,
					request.state as state,
					request.holiday_type,
					request.date_from as date_from,
					request.date_to as date_to,
					request.payslip_status as payslip_status,
					'request' as leave_type,
					request.work_suspension_id as work_suspension_id
				from hr_leave as request) leaves
			);
		""")

