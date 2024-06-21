# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _

class UpdateMoveItWizard(models.TransientModel):
	_name = 'update.move.it.wizard'
	_description = 'Update Move IT Wizard'

	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')

	def importar(self):
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
		except:
			raise Warning(_("Archivo invalido!"))

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 2:
					values = ({'id':line[0],
								'voucher':line[1],
								})
				elif len(line) > 2:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))
				
				self.update_move_id(values)
		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CON EXITO LOS ASIENTOS.')

	def update_move_id(self, values):
		if str(values.get('id')) == '':
			raise Warning(_('El campo "id" no puede estar vacio.'))

		id = int(float(values.get("id")))

		self.env.cr.execute("""UPDATE account_move set name = '%s' where id = %d"""%(values.get('voucher'),id))

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_update_number_move_template',
			 'target': 'new',
			 }