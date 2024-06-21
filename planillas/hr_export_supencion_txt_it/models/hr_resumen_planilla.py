# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import decimal
import base64
import time
from odoo.exceptions import UserError, ValidationError
from xlsxwriter.workbook import Workbook

#
# class HrMainParameter(models.Model):
# 	_inherit = 'hr.main.parameter'
#
# 	hr_suspension_type_ids = fields.Many2many('hr.suspension.type','rel_suspencion_param','parameter_id','suspencion_id','Suspenciones aceptadas')

class HrResumenPlanilla(models.Model):
	_inherit = 'hr.resumen.planilla'

	def export_plame_suspencion(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.snl' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			for payslip in payslip_run.slip_ids:
				tdoc = payslip.contract_id.employee_id.type_document_id.sunat_code.rjust(2,'0') if payslip.contract_id.employee_id.type_document_id.sunat_code else ''
				ndoc = payslip.contract_id.employee_id.identification_id
				ndias = 0
				lineas = payslip.contract_id.work_suspension_ids.filtered(lambda linea: linea.periodo_id.id == self.periodo_id.id)

				memoria=[]
				for line in lineas:
					# print("line",line.suspension_type_id)
					if line.suspension_type_id.code in memoria:
						continue
					total_dias = self.env['hr.work.suspension'].search([('periodo_id', '=', self.periodo_id.id),('contract_id', '=',payslip.contract_id.id),
																		('suspension_type_id', '=',line.suspension_type_id.id)]).mapped('days')
					# print("total_dias",sum(total_dias))

					f.write("%s|%s|%s|%s|\r\n" % (
						tdoc,
						ndoc,
						line.suspension_type_id.code,
						sum(total_dias)
					))
					memoria.append(line.suspension_type_id.code)
					# print("memoria",memoria)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.snl' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))