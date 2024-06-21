# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning , UserError
import base64
from datetime import date, datetime, timedelta

class ConvertRecxhonWizard(models.TransientModel):
	_name = 'convert.recxhon.wizard'
	_description = 'Convert Recxhon Wizard'	

	account_id = fields.Many2one('account.account',string='Cuenta')
	journal_id = fields.Many2one('account.journal',string='Diario')
	document_file = fields.Binary(string='Archivo')
	name_file = fields.Char(string='Nombre de Archivo')

	def load_lines(self):
		self.ensure_one()
		if self.document_file:
			MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
			if not MainParameter.dir_create_file:
				raise UserError('No se ha configurado una ruta de descarga dentro de Parametros Principales de Contabilidad')

			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']
			workbook = Workbook(MainParameter.dir_create_file +'HONORARIOS.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("HONORARIOS")
			worksheet.set_tab_color('blue')

			HEADERS = ['INVOICE ID','PARTNER','CURRENCY','PRODUCT','ACCOUNT','QUANTITY','UOM','DESCRIPTION','PRICE',
			'DISCOUNT','SALESPERSON','TAX','DATE','INVOICE DATE','TD','NROCOMPROBANTE','GLOSA','CUENTAANALITICA']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			dateformat = workbook.add_format({'num_format':'yyyy-mm-dd'})
			dateformat.set_align('justify')
			dateformat.set_align('vcenter')
			dateformat.set_border(style=1)
			dateformat.set_font_size(10)
			dateformat.set_font_name('Times New Roman')

			file_content = base64.decodestring(self.document_file)
			file_content = file_content.decode("utf-8")
			process_file = file_content.split("\r\n")

			for i in range(len(process_file)-1):
				if i==0:
					continue
				else:
					data = process_file[i].split('|')
					try:
						if data[3] == 'NO ANULADO':
							datee = datetime.strptime(data[0],'%d/%m/%Y').date()
							worksheet.write(x,0,'invoice%d'%(x),formats['especial1'])
							worksheet.write(x,1,data[5] if data[5] else '',formats['especial1'])
							worksheet.write(x,2,'PEN' if data[11] == 'SOLES' else 'USD',formats['especial1'])
							worksheet.write(x,3,'',formats['especial1'])
							worksheet.write(x,4,'',formats['especial1'])
							worksheet.write(x,5,1,formats['numberdos'])
							worksheet.write(x,6,'Unidades',formats['especial1'])
							worksheet.write(x,7,data[9] if data[9] else '',formats['especial1'])
							worksheet.write(x,8,data[12] if data[12] else 1,formats['numberdos'])
							worksheet.write(x,9,0,formats['numberdos'])
							worksheet.write(x,10,self.env.user.name,formats['especial1'])
							worksheet.write(x,11,'4TA0%' if float(data[13]) == 0 else '4TA8%',formats['numberdos'])
							worksheet.write(x,12,datee,dateformat)
							worksheet.write(x,13,datee,dateformat)
							worksheet.write(x,14,'02',formats['especial1'])
							worksheet.write(x,15,data[2] if data[2] else '',formats['especial1'])
							worksheet.write(x,16,data[9] if data[9] else '',formats['especial1'])
							worksheet.write(x,17,'',formats['especial1'])
							x += 1
					except Exception as e:
						raise UserError(e)

			widths = [10,12,11,10,10,10,8,20,8,10,15,6,10,14,5,20,20,15]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()

			f = open(MainParameter.dir_create_file +'HONORARIOS.xlsx', 'rb')
			return self.env['popup.it'].get_file('HONORARIOS.xlsx',base64.encodestring(b''.join(f.readlines())))


	def import_invoices(self):
		self.ensure_one()
		if self.document_file:
			if not self.account_id:
				raise UserError('Se necesita de una cuenta para crear las facturas')
			if not self.journal_id:
				raise UserError('Se necesita de un diario para crear las facturas')
			file_content = base64.decodestring(self.document_file)
			file_content = file_content.decode("utf-8")
			process_file = file_content.split("\r\n")
			import_id = self.env['delete.account.move.import'].create({
						'date': fields.Date.context_today(self),
						'company_id':self.env.company.id
					})
			invoice_obj = self.env['account.move']
			for i in range(len(process_file)-1):
				if i==0:
					continue
				else:
					data = process_file[i].split('|')
					try:
						if data[3] == 'NO ANULADO':
							partner_id = self.find_partner(data[5] if data[5] else '')
							currency_id = self.find_currency('PEN' if data[11] == 'SOLES' else 'USD')
							salesperson_id = self.env.uid
							inv_date = datetime.strptime(data[0],'%d/%m/%Y').date()
							type_document_id = self.find_type_document('02')

							inv_id = invoice_obj.create({
								'name': '/',
								'partner_id' : partner_id.id,
								'currency_id' : currency_id.id,
								'invoice_user_id':salesperson_id,
								'type' : 'in_invoice',
								'date':inv_date,
								'invoice_date':inv_date,
								'journal_id' : self.journal_id.id,
								'type_document_id' : type_document_id.id,
								'ref' : data[2] if data[2] else '',
								'glosa': data[9] if data[9] else '',
								'company_id' : self.env.company.id
							})

							tax_ids = []
							tax_name = '4TA0%' if float(data[13]) == 0 else '4TA8%'
							tax = self.env['account.tax'].search([('name', '=', tax_name), ('type_tax_use', '=', 'purchase')],limit=1)
							if not tax:
								raise Warning('"%s" Tax not in your system' % tax_name)
							tax_ids.append(tax.id)

							product_uom = self.env['uom.uom'].search([('name', '=', 'Unidades')],limit=1)
							if not product_uom:
								raise Warning(' "Unidades" Product UOM category is not available.')

							vals = {
								'quantity' : 1,
								'price_unit' :data[12] if data[12] else 1,
								'discount':0,
								'name' : data[9] if data[9] else '',
								'account_id' : self.account_id.id,
								'product_uom_id' : product_uom.id,
								'company_id' : self.env.company.id
							}
							if tax_ids:
								vals.update({'tax_ids':([(6,0,tax_ids)])})

							inv_id.write({'invoice_line_ids' :([(0,0,vals)]), 'code_import_invoice': import_id.id })
							inv_id._get_currency_rate()
							inv_id._onchange_tc_per()
							inv_id._compute_amount()
							inv_id.flush()

					except Exception as e:
						raise UserError(e)

			return {
				'view_mode': 'form',
				'view_id': self.env.ref('import_invoice.view_delete_account_move_import_form').id,
				'res_model': 'delete.account.move.import',
				'type': 'ir.actions.act_window',
				'res_id': import_id.id,
			}

						

	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise Warning(_(' "%s" Currency are not available.') % name)

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('No existe un Partner con el Nro de Documento "%s"') % name)

	def find_type_document(self,name):
		type_document_search = self.env['einvoice.catalog.01'].search([('code','=',str(name))],limit=1)
		if type_document_search:
			return type_document_search
		else:
			raise Warning(_('No existe un Tipo de Comprobante con el Codigo"%s"') % name)