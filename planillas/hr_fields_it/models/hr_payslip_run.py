# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *
from math import modf

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	slip_ids = fields.One2many(states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
	calcular_af = fields.Boolean(string='Calcular Asign. Familiar', default=False)
	type_id = fields.Many2one('hr.payroll.structure.type',string='Tipo de Planilla', required=True)
	partner_id = fields.Many2one('res.partner', string='Cliente')
	contract_type = fields.Selection([('S', 'De Suplencia'),
								  	('O', 'Ocasional')
								], string='Tipo de Contrato')

	def action_open_payslips(self):
		rec = super(HrPayslipRun, self).action_open_payslips()
		rec['context'] = {'default_payslip_run_id': self.id}
		return rec

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

	def get_employees_news(self):
		wizard = self.env['hr.employee.news.wizard'].create({
			'payslip_run_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_hr_employee_news_wizard' % module)
		return {
			'name':u'Seleccionar Empleados',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.employee.news.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def tab_payroll(self):
		return {
			'name': 'Planilla Tabular',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'hr.planilla.tabular.salary.wizard',
			'context': {'default_payslip_run_id': self.id},
			'target': 'new',
		}