# -*- coding:utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from math import modf

class HrPayslipRunConsolidado(models.Model):
	_inherit = 'hr.resumen.planilla'


	def vouchers_by_lot(self):
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		return self.env['hr.payslip'].get_vouchers(self.slip_ids)
