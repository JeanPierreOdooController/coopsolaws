# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date
import inspect
from num2words import num2words

class hr_contract(models.Model):
	_inherit = 'hr.contract'

	contract_type_id = fields.Many2one('hr.contract.type', "Modelo Contrato")

	def export_contract(self):
		return self.env.ref('hr_print_contract.action_report_contract_employee').report_action(self)

	def send_contract_email(self):
		for rec in self:
			template = self.env.ref('hr_print_contract.report_contract_employee')
			email_values = {
				'email_to': rec.employee_id.work_email,
			}
			template.send_mail(rec.id, force_send=True, email_values=email_values)

class ContractType(models.Model):
	_name = 'hr.contract.type'
	_description = 'Contract Type'

	name = fields.Char(string="Nombre",required=True)
	contract_html = fields.Html('Contrato')