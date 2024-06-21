# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	#####VACACIONES######
	# vaca_input_id = fields.Many2one('hr.payslip.input.type', string='Input Vacaciones')

	def check_vacation_values(self):
		if not self.vacation_input_id or \
			not self.bonus_sr_ids or \
			not self.commission_sr_ids or \
			not self.extra_hours_sr_id or \
			not self.basic_sr_id or \
			not self.household_allowance_sr_id or \
			not self.lack_wd_id:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Vacaciones del Menu de Parametros Principales')