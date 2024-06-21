# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDaysType(models.Model):
	_inherit = 'hr.payslip.worked_days.type'

	convert_days = fields.Boolean(string="Convertir Horas a Dias", default=False)