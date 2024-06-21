# -*- encoding: utf-8 -*-
from odoo import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError
import base64

class ImportfortnightLine(models.TransientModel):
	_name = 'import.fortnight.line'
	_description = 'Importa y Actualiza'

	name = fields.Char('name')
	fortnight_id = fields.Many2one('hr.quincenales', string='Quincena', readonly=True)
	file = fields.Binary('Excel')
	name_file = fields.Char('name_file')
	type = fields.Selection([
		('income', 'Ingresos'),
		('discounts', 'Descuentos'),
		('out_of_fortnight', 'Fuera de Quincena')
	], string='Tipo', default="income")


	def value_fields(self,code):
		for i in self:
			data = False
			if i.type in ('income','discounts'):
				data = self.env['hr.salary.rule'].sudo().search([('code', '=', code)],limit=1)
			else:
				data = self.env['hr.payslip.input.type'].sudo().search([('code', '=', code)],limit=1)
			if data:
				return data.id
			else:
				raise UserError (u'No se encontro el concepto o entrada (%s)'%(code))


	def action_update(self):
		if self:
			try:
				file_string = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
				file_string.write(binascii.a2b_base64(self.file))
				file_string.close()
				book = xlrd.open_workbook(file_string.name)
				sheet = book.sheet_by_index(0)
			except:
				raise UserError(_("Por favor elija el archivo correcto"))
			starting_line = True
			cont=0
			errors = ''
			for i in range(sheet.nrows):
				if starting_line:
					starting_line = False
				else:
					line = list(sheet.row_values(i))
					cont += 1
					if line[0] or line[3] or line[4]:
						concepto = self.value_fields(line[3].strip())
						fortnight_line = self.fortnight_id.quincenales_lines.filtered(lambda l: l.codigo_trabajador == str(line[0]))
						if fortnight_line:
							lines = []
							concep_line = False
							if self.type in ('income','discounts'):
								if not line[1]:
									lines.append((0, 0, {'concepto_id': concepto,
														 'monto': float(line[4]),
														 }))
									if self.type == 'discounts':
										fortnight_line.write({'quincenales_descuentos_lines': lines})
									else:
										fortnight_line.write({'quincenales_ingresos_lines': lines})
								else:
									if self.type == 'discounts':
										concep_line = fortnight_line.quincenales_descuentos_lines.filtered(lambda l: l.id == int(line[1]))
									else:
										concep_line = fortnight_line.quincenales_ingresos_lines.filtered(lambda l: l.id == int(line[1]))
									if concep_line:
										concep_line.concepto_id = concepto
										concep_line.monto = float(line[4])
							else:
								if not line[5]:
									raise UserError(u"Para los tipo FUERA DE QUINCENA ES OBLIGATORIO LA COLUMNA TIPO EN EL EXCEL")
								else:
									if line[5] not in ('Ingreso','Descuento'):
										raise UserError(u"El Tipo solo puede ser Ingreso o Descuento")
								if not line[1]:
									lines.append((0, 0, {'name_input_id': concepto,
														 'amount': float(line[4]),
														 'type': 'in' if str(line[5]) == 'Ingreso' else 'out' if str(line[5]) == 'Descuento' else ''
														 }))
									fortnight_line.write({'quincenales_conceptos_lines': lines})
								else:
									concep_line = fortnight_line.quincenales_conceptos_lines.filtered(lambda l: l.id == int(line[1]))
									if concep_line:
										concep_line.name_input_id = concepto
										concep_line.amount = float(line[4])
										concep_line.type = 'in' if str(line[5]) == 'Ingreso' else 'out' if str(line[5]) == 'Descuento' else ''
								fortnight_line.add_concept()
						else:
							errors += 'EN LA FILA %s FALTA DATOS\n\n'%(str(cont))
					else:
						errors += 'Este pago Quincenal no tiene ningun Trabajador cargado'
			if errors != '':
				raise UserError(_(errors))

			return self.env['popup.it'].get_message('SE ACTUALIZÓ CORRECTAMENTE SUS REGISTROS')


	def download_template(self):
		for i in self:
			if i.fortnight_id:
				if i.type == 'income':
					return {
						'type' : 'ir.actions.act_url',
						'url': '/web/binary/download_template_update_income_fortnight_lines/%d'%(i.fortnight_id.id),
						'target': 'new',
					}
				elif  i.type == 'discounts':
					return {
						'type' : 'ir.actions.act_url',
						'url': '/web/binary/download_template_update_discounts_fortnight_lines/%d'%(i.fortnight_id.id),
						'target': 'new',
					}
				else:
					return {
						'type' : 'ir.actions.act_url',
						'url': '/web/binary/download_template_out_of_fortnight_update_fortnight_lines/%d'%(i.fortnight_id.id),
						'target': 'new',
					}
			