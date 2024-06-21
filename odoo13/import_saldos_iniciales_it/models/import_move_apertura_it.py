# -*- coding: utf-8 -*-

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo.osv import osv
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class ImportMoveAperturaIt(models.Model):
	_name = 'import.move.apertura.it'
	_description = 'Import Move Apertura It'

	fecha_contable = fields.Date(string='Fecha Contable')
	account_descargo_mn = fields.Many2one('account.account',string='Cuenta de Descargo Soles')
	account_descargo_me = fields.Many2one('account.account',string='Cuenta de Descargo Dolares')
	partner_descargo = fields.Many2one('res.partner',string='Partner Descargo')
	document_descargo = fields.Char(string='Documento Descargo')
	document_file = fields.Binary(string='Excel', help="El archivo Excel debe ir con la cabecera: n_ruc, n_razonsoc, n_fecha_emision, n_fecha_vencimiento, n_vendedor, n_tipo_doc, n_numero, n_moneda, n_saldo_mn, n_saldo_me, n_cuenta, n_tipo_cambio, n_doc_origin")
	name_file = fields.Char(string='Nombre de Archivo')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],string='Estado',default='draft')
	journal_id = fields.Many2one('account.journal',string='Diario')
	is_opening_close = fields.Boolean(string='Apertura/Cierre',default=False)

	detalle = fields.One2many('import.move.apertura.it.line','wizard_id','Detalle')
	type = fields.Selection([('out','Cliente'),('in','Proveedor')],string='Tipo')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	_rec_name = 'name_file'
	
	@api.model
	def create(self,vals):	
		if len( self.env['import.move.apertura.it'].search([('state','in',('draft','cancel')),('type','=',self.env.context.get('default_type'))])) >0:
			raise UserError('Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(ImportMoveAperturaIt,self).create(vals)
		t.refresh()
		return t

	def write(self,vals):
		if len( self.env['import.move.apertura.it'].search([('state','in',('draft','cancel')),('id','!=',self.id),('type','=',self.type)])) >0:
			raise UserError('Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(ImportMoveAperturaIt,self).write(vals)
		self.refresh()
		return t
	
	def unlink(self):
		if self.state != 'draft':
			raise osv.except_osv('No se puede eliminar una importacion en proceso.')
		for i in self.detalle:
			i.unlink()
		t = super(ImportMoveAperturaIt,self).unlink()
		return t

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

		lineas = []

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 13:
					date_string = None
					date_due_string = None
					if line[2] != '':
						a1 = int(float(line[2]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					if line[3] != '':
						a1 = int(float(line[3]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_due_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = (0,0,{'n_ruc': line[0],
								'n_razonsoc': line[1],
								'n_fecha_emision': date_string,
								'n_fecha_vencimiento': date_due_string,
								'n_vendedor':line[4],
								'n_tipo_doc':line[5],
								'n_numero':line[6],
								'n_moneda':line[7] if line[7] else 'PEN',
								'n_saldo_mn':line[8],
								'n_saldo_me':line[9],
								'n_cuenta':line[10],
								'n_tipo_cambio':line[11],
								'n_doc_origin':line[12] or None,
								})
				elif len(line) > 13:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))

				lineas.append(values)

		self.write({'detalle': lineas})

		self.env.cr.execute("""
			
			update import_move_apertura_it_line set

			ruc = T.v1,
			razon_social = T.v2,
			fecha_emision = T.v3::date,
			fecha_vencimiento = T.v4::date,
			vendedor = T.v5,
			tipo_doc = T.v6,
			numero = T.v7,
			moneda = T.v8,
			saldo_mn = T.v9::numeric,
			saldo_me = T.v10::numeric,
			cuenta = T.v11,
			tipo_cambio = T.v12::numeric,
			doc_origin = T.v13

			from (
			select 
			iaa.id as id,
			iaa.n_ruc as v1,
			rp1.id as v2,
			iaa.n_fecha_emision as v3,
			iaa.n_fecha_vencimiento as v4,
			ru.id as v5,
			ec.id as v6,
			iaa.n_numero as v7,
			rc.id as v8,
			iaa.n_saldo_mn as v9,
			iaa.n_saldo_me as v10,
			aa.id as v11,
			iaa.n_tipo_cambio as v12,
			iaa.n_doc_origin as v13

			from import_move_apertura_it_line iaa
			left join res_partner rp on rp.vat = iaa.n_ruc
			left join res_partner rp1 on rp1.id = rp.commercial_partner_id
			left join res_partner rpp2 on rpp2.name = iaa.n_vendedor
			left join res_users ru on ru.partner_id = rpp2.id
			left join einvoice_catalog_01 ec on ec.code = iaa.n_tipo_doc
			left join res_currency rc on rc.name = iaa.n_moneda
			left join account_account aa on aa.code = iaa.n_cuenta and aa.company_id = %s
			where iaa.wizard_id = %s ) T where T.id = import_move_apertura_it_line.id
		 """ % (str(self.company_id.id),str(self.id)))

		self.env.cr.execute("""
						select ruc,
						razon_social,
						vendedor,
						n_vendedor,
						cuenta,
						n_cuenta
						from import_move_apertura_it_line
						where wizard_id = %s
			""" % (str(self.id)))

		problemas = ""
		for i in self.env.cr.fetchall():
			if not i[1]:
				problemas += "No se encontro el partner: " + i[0] + '\n'
			if not i[4]:
				problemas += "No se encontro la cuenta : " + i[5] + '\n'
			if i[3]:
				if not i[2]:
					problemas += "No se encontro el Vendedor: " + i[3] + '\n'

		if problemas != "":
			raise osv.except_osv(problemas)

		self.env.cr.execute("""select count(n_ruc) as cont,n_ruc,n_tipo_doc,n_numero,n_cuenta from import_move_apertura_it_line  where wizard_id = %s
							group by n_ruc,n_tipo_doc,n_numero,n_cuenta
							having count(n_ruc)>1""" % (str(self.id)))

		for i in self.env.cr.fetchall():
			problemas+= "Existen "+str(i[0]) + " lineas duplicadas con los siguientes datos: \n"
			problemas+= u"RUC: "+str(i[1]) + " \n"
			problemas+= "Tipo Documento: "+str(i[2]) + " \n"
			problemas+= "Nro Comprobante: "+str(i[3]) + " \n"
			problemas+= "Cuenta: "+str(i[4]) + " \n \n"

		if problemas != "":
			raise osv.except_osv(problemas)

		############################## CREACION DE ASIENTOS CONTABLES #######################################
		parametros = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		self.env.cr.execute("""select razon_social,fecha_emision,fecha_vencimiento,vendedor,tipo_doc,numero,moneda,saldo_mn,saldo_me,cuenta,tipo_cambio,doc_origin
							from import_move_apertura_it_line where wizard_id = %s order by id """ % (str(self.id)))

		data = self.env.cr.fetchall()
		document_code = self.env['einvoice.catalog.01'].search([('code','=','00')],limit=1)
		for acc in data:
			currency = self.env['res.currency'].search([('id','=',acc[6])],limit=1)
			lineas = []
			if self.type == 'out':
				type_invoice = ('out_refund' if parametros.dt_national_credit_note.id == acc[4] else 'out_invoice') if parametros.dt_national_credit_note else 'out_invoice'
				if currency.name != 'PEN':
					vals = (0,0,{
						'account_id': self.account_descargo_me.id,
						'partner_id': self.partner_descargo.id,
						'type_document_id': document_code.id,
						'nro_comp': self.document_descargo,
						'name': 'SALDOS DE APERTURA',
						'currency_id': currency.id,
						'amount_currency': acc[8]*-1,
						'debit': 0 if acc[7] > 0 else abs(acc[7]),
						'credit': acc[7] if acc[7] > 0 else 0,
						'price_subtotal':acc[8],
						'price_total':acc[8],
						'price_unit':acc[8],
						'date_maturity':acc[2],
						'company_id': self.company_id.id,
						'tc': acc[10],
						'exclude_from_invoice_tab': False,
						'balance':acc[7]*-1,
					})
					lineas.append(vals)
					vals = (0,0,{
						'account_id': acc[9],
						'partner_id': acc[0],
						'type_document_id':acc[4],
						'nro_comp': acc[5],
						'name': 'SALDOS DE APERTURA',
						'currency_id': currency.id,
						'amount_currency': acc[8],
						'debit': acc[7] if acc[7] > 0 else 0,
						'credit': 0 if acc[7] > 0 else abs(acc[7]),
						'price_subtotal':acc[8]*-1,
						'price_total':acc[8]*-1,
						'price_unit':acc[8]*-1,
						'date_maturity':acc[2],
						'company_id': self.company_id.id,
						'tc': acc[10],
						'exclude_from_invoice_tab': True,
						'balance':acc[7],
						'amount_residual': acc[7],
						'amount_residual_currency': acc[8],
					})
					lineas.append(vals)
				else:
					vals = (0,0,{
						'account_id': self.account_descargo_mn.id,
						'partner_id': self.partner_descargo.id,
						'type_document_id':document_code.id,
						'nro_comp': self.document_descargo,
						'name': 'SALDOS DE APERTURA',
						'debit': 0 if acc[7] > 0 else abs(acc[7]),
						'credit': acc[7] if acc[7] > 0 else 0,
						'price_subtotal':acc[7],
						'price_total':acc[7],
						'price_unit':acc[7],
						'company_id': self.company_id.id,
						'exclude_from_invoice_tab': False,
						'date_maturity':acc[2],
						'balance':acc[7]*-1,
					})
					lineas.append(vals)
					vals = (0,0,{
						'account_id': acc[9],
						'partner_id': acc[0],
						'type_document_id':acc[4],
						'nro_comp': acc[5],
						'name': 'SALDOS DE APERTURA',
						'debit': acc[7] if acc[7] > 0 else 0,
						'credit': 0 if acc[7] > 0 else abs(acc[7]),
						'price_subtotal':acc[7]*-1,
						'price_total':acc[7]*-1,
						'price_unit':acc[7]*-1,
						'company_id': self.company_id.id,
						'exclude_from_invoice_tab': True,
						'date_maturity':acc[2],
						'balance':acc[7],
						'amount_residual': acc[7],
					})
					lineas.append(vals)
			else:
				type_invoice = ('in_refund' if parametros.dt_national_credit_note.id == acc[4] else 'in_invoice') if parametros.dt_national_credit_note else 'in_invoice'
				if currency.name != 'PEN':
					vals = (0,0,{
						'account_id': self.account_descargo_me.id,
						'partner_id': self.partner_descargo.id,
						'type_document_id':document_code.id,
						'nro_comp': self.document_descargo,
						'name': 'SALDOS DE APERTURA',
						'currency_id': currency.id,
						'amount_currency': acc[8],
						'debit': acc[7] if acc[7] > 0 else 0,
						'credit': 0 if acc[7] > 0 else abs(acc[7]),
						'price_subtotal':acc[8],
						'price_total':acc[8],
						'price_unit':acc[8],
						'date_maturity':acc[2],
						'company_id': self.company_id.id,
						'tc': acc[10],
						'exclude_from_invoice_tab': False,
						'balance':acc[7],
					})
					lineas.append(vals)
					vals = (0,0,{
						'account_id': acc[9],
						'partner_id': acc[0],
						'type_document_id':acc[4],
						'nro_comp': acc[5],
						'name': 'SALDOS DE APERTURA',
						'currency_id': currency.id,
						'amount_currency': acc[8]*-1,
						'debit': 0 if acc[7] > 0 else abs(acc[7]),
						'credit': acc[7] if acc[7] > 0 else 0,
						'price_subtotal':acc[8]*-1,
						'price_total':acc[8]*-1,
						'price_unit':acc[8]*-1,
						'date_maturity':acc[2],
						'company_id': self.company_id.id,
						'tc': acc[10],
						'exclude_from_invoice_tab': True,
						'balance':acc[7]*-1,
						'amount_residual': acc[7]*-1,
						'amount_residual_currency': acc[8]*-1,
					})
					lineas.append(vals)
				else:
					vals = (0,0,{
						'account_id': self.account_descargo_mn.id,
						'partner_id': self.partner_descargo.id,
						'type_document_id':document_code.id,
						'nro_comp': self.document_descargo,
						'name': 'SALDOS DE APERTURA',
						'debit': acc[7] if acc[7] > 0 else 0,
						'credit': 0 if acc[7] > 0 else abs(acc[7]),
						'price_subtotal':acc[7],
						'price_total':acc[7],
						'price_unit':acc[7],
						'company_id': self.company_id.id,
						'exclude_from_invoice_tab': False,
						'date_maturity':acc[2],
						'balance':acc[7],
					})
					lineas.append(vals)
					vals = (0,0,{
						'account_id': acc[9],
						'partner_id': acc[0],
						'type_document_id':acc[4],
						'nro_comp': acc[5],
						'name': 'SALDOS DE APERTURA',
						'debit': 0 if acc[7] > 0 else abs(acc[7]),
						'credit': acc[7] if acc[7] > 0 else 0,
						'price_subtotal':acc[7]*-1,
						'price_total':acc[7]*-1,
						'price_unit':acc[7]*-1,
						'company_id': self.company_id.id,
						'exclude_from_invoice_tab': True,
						'date_maturity':acc[2],
						'balance':acc[7]*-1,
						'amount_residual': acc[7]*-1,
					})
					lineas.append(vals)

			move_id = self.env['account.move'].create({
			'partner_id': acc[0],
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.fecha_contable,
			'invoice_date': acc[1],
			'invoice_date_due':acc[2],
			'type_document_id':acc[4],
			'line_ids':lineas,
			'ref': acc[5],
			'currency_rate':acc[10] if acc[10] else 1,
			'glosa':'SALDOS DE APERTURA',
			'apertura_id':self.id,
			'currency_id':currency.id if currency.name != 'PEN' else self.env.company.currency_id.id,
			'is_opening_close':self.is_opening_close,
			'invoice_user_id':acc[3] if acc[3] else self.env.user.id,
			'invoice_payment_state': 'not_paid',
			'amount_untaxed': acc[8] if currency.name != 'PEN' else acc[7],
			'amount_total': acc[8] if currency.name != 'PEN' else acc[7],
			'amount_residual': acc[8] if currency.name != 'PEN' else acc[7],
			'amount_untaxed_signed': acc[7]*-1 if self.type == 'in' else acc[7],
			'amount_total_signed': acc[7]*-1 if self.type == 'in' else acc[7],
			'amount_residual_signed': acc[7]*-1 if self.type == 'in' else acc[7],
			'invoice_origin': acc[11],
			'type':type_invoice})
			
			move_id._get_ref()
			move_id.post()

		self.state = 'import'

	def eliminar(self):
		accounts = self.env['account.move'].search([('apertura_id','=',self.id)])
		accounts.button_cancel()
		accounts.line_ids.unlink()
		accounts.name = "/"
		accounts.unlink()

		self.env.cr.execute(""" 
			DELETE FROM import_move_apertura_it_line WHERE wizard_id = """+str(self.id)+""";
			""")

		self.state = 'cancel'

	def borrador(self):
		self.state = 'draft'

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_initial?model=import.move.apertura.it&id=%s'%(self.id),
			 'target': 'new',
			 }

class ImportMoveAperturaItLine(models.Model):
	_name = 'import.move.apertura.it.line'
	_description = 'Import Move Apertura It Line'

	wizard_id = fields.Many2one('import.move.apertura.it','Importacion')
	ruc = fields.Char(string='RUC')
	razon_social = fields.Many2one('res.partner',string='Razon Social')
	fecha_emision = fields.Date(string='Fecha Emision')
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento')
	vendedor = fields.Many2one('res.users',string='Vendedor')
	tipo_doc = fields.Many2one('einvoice.catalog.01',string='Tipo Doc.')
	numero = fields.Char(string='Numero')
	moneda = fields.Many2one('res.currency',string='Moneda')
	saldo_mn = fields.Float(string='Saldo MN')
	saldo_me = fields.Float(string='Saldo ME')
	cuenta = fields.Many2one('account.account',string='Cuenta')
	tipo_cambio = fields.Float(string='Tipo Cambio',digits=(12,4))
	doc_origin = fields.Char(string='Doc Origen')

	n_ruc = fields.Char('Campo 1')
	n_razonsoc = fields.Char('Campo 2')
	n_fecha_emision = fields.Char('Campo 3')
	n_fecha_vencimiento = fields.Char('Campo 4')
	n_vendedor = fields.Char('Campo 5')
	n_tipo_doc = fields.Char('Campo 6')
	n_numero = fields.Char('Campo 7')
	n_moneda = fields.Char('Campo 8')
	n_saldo_mn = fields.Char('Campo 9')
	n_saldo_me = fields.Char('Campo 10')
	n_cuenta = fields.Char('Campo 11')
	n_tipo_cambio = fields.Char('Campo 12',digits=(12,4))
	n_doc_origin = fields.Char('Campo 13')