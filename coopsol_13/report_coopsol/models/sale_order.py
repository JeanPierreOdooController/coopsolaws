# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import base64
from io import BytesIO
import re
import uuid

import codecs
import pprint
import decimal

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Group, Line
import time

class saleOrder(models.Model):
	_inherit = 'sale.order'
	acc_number_it = fields.Many2one('res.partner.bank',compute="get_acc_number_it")
	account_bank = fields.Char(compute="get_acc_number_it")
	def get_acc_number_it(self):
		for record in self:
			record.acc_number_it = False
			accountx = self.env['res.partner.bank'].search(
				[('is_account_detraction', '=', True), ('partner_id', '=', record.company_id.partner_id.id)], limit=1)
			if accountx:
				record.acc_number_it = accountx.id

			account = self.env['res.partner.bank'].search(
				[('is_account_detraction', '=', False), ('partner_id', '=', self.company_id.partner_id.id)], limit=1)

			kk = 'CTA. CTE. %s SOLES: %s | %s' % (
			account.bank_id.name if account.bank_id else '', account.acc_number if account.acc_number else '',
			account.cci if account.cci else '')
			#raise ValueError(record._get_account_cte())
			record.account_bank = kk


	def _get_account_detraction(self):
		account = self.env['res.partner.bank'].search([('is_account_detraction','=',True),('partner_id','=',self.company_id.partner_id.id)],limit=1)


		return 'NUMERO DE CUENTA DE DETRACCION: %s' % (account.acc_number if account.acc_number else '')

	def _get_account_cte(self):
		account = self.env['res.partner.bank'].search([('is_account_detraction','=',False),('partner_id','=',self.company_id.partner_id.id)],limit=1)


		return 'CTA. CTE. %s SOLES: %s | %s' % (account.bank_id.name if account.bank_id else '',account.acc_number if account.acc_number else '', account.cci if account.cci else '')

	def get_sale_order_print_it(self):
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		param_sale = self.env['main.parameter.sale'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param_sale:
			raise UserError('Configure sus parametros Principales de Ventas')

		param_sale._check_parameters()

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "orden_venta.pdf"

		archivo_pdf = SimpleDocTemplate(direccion + name_file, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)

		elements = []
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 7.5, fontName="Helvetica-Bold" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 7.5, fontName="Helvetica-Bold", leading=8)
		style_right = ParagraphStyle(name='Justify', alignment=TA_RIGHT , fontSize = 7.5, fontName="Helvetica-Bold")
		style_center_cell = ParagraphStyle(name='Justify', alignment=TA_CENTER , fontSize = 7.5, fontName="Helvetica")
		style_left_cell = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 7.5, fontName="Helvetica")
		style_right_cell = ParagraphStyle(name='Justify', alignment=TA_RIGHT , fontSize = 7.5, fontName="Helvetica")

		company = self.company_id

		I = ReportBase.create_image(company.logo, direccion + 'logo.jpg', param_sale.width, param_sale.height)
		data = [[I if I else '','',Paragraph('# COT: %s - %s'%(self.name,str(self.date_order.year)),style_title)],
				['','',''],
				['','',''],
				['','','']]
		t = Table(data, [4.5*cm,10 * cm,4.5*cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
							   ('GRID',(2, 0), (2, 0), 1.5, colors.black),
							   ('SPAN',(0,0),(0,3))]))
		elements.append(t)
		elements.append(Spacer(10, 20))

		data_header = [[Paragraph(u'CLIENTE',style_form),Paragraph(': '+self.partner_id.name,style_form),Paragraph(u'ENCARGADO',style_form),Paragraph(': '+(self.contact_id.name if self.contact_id else ''),style_form)],
		[Paragraph(u'DIRECCIÓN',style_form),Paragraph(': '+(self.partner_id.street if self.partner_id.street else ''),style_form),Paragraph(u'EMAIL',style_form),Paragraph(': '+(self.partner_id.email if self.partner_id.email else ''),style_form)],
		[Paragraph(u'PROYECTO',style_form),Paragraph(': '+(self.analytic_account_id.name if self.analytic_account_id else ''),style_form),Paragraph(u'RUC',style_form),Paragraph(': '+(self.partner_id.vat if self.partner_id.vat else ''),style_form)],
		['','','',''],
		[Paragraph(u'RAZÓN SOCIAL',style_form),Paragraph(': '+company.name,style_form),Paragraph(u'EMAIL',style_form),Paragraph(': '+(company.partner_id.email if company.partner_id.email else ''),style_form)],
		[Paragraph(u'DIRECCIÓN',style_form),Paragraph(': '+(company.street if company.street else ''),style_form),Paragraph(u'RUC',style_form),Paragraph(': '+(company.partner_id.vat if company.partner_id.vat else ''),style_form)],
		[Paragraph(u'TELEFONOS',style_form),Paragraph(': '+(company.partner_id.mobile if company.partner_id.mobile else ''),style_form),Paragraph(u'FECHA',style_form),Paragraph(': '+self.date_order.strftime('%d-%m-%Y'),style_form)],
		[Paragraph(u'REFERENCIA',style_form),Paragraph(': '+(company.reference if company.reference else ''),style_form),'','']]
		
		
		t3 = Table(data_header, colWidths=[2.2*cm,8.6*cm,2.4*cm,6.5*cm])
		t3.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							('VALIGN', (0, 0), (-1, -1), 'TOP'),
							('SPAN',(1,7),(3,7))
							]))

		elements.append(t3)
		elements.append(Spacer(1, 24))

		color_service = colors.HexColor(param_sale.color_service)
		color_head = colors.HexColor(param_sale.color_head)
		color_section = colors.HexColor(param_sale.color_section)
		color_subtotal = colors.HexColor(param_sale.color_subtotal)

		data_content = [[Paragraph(self.service_type_id.name if self.service_type_id else '',style_title),'','','',''],
			[Paragraph(u'ITEM',style_title),Paragraph(u'DESCRIPCIÓN',style_title),Paragraph(u'UNIDAD',style_title),
			Paragraph(u'P. UNIT.',style_title),Paragraph(u'<b>SUB TOTAL</b>',style_title)]]
		x = 2
		array_style = [('ALIGN', (0, 0), (0, 0), 'LEFT'),
						('VALIGN', (0, 0), (-1, -1), 'TOP'),
						('BACKGROUND', (0, 0), (4, 0),color_service),
						('BACKGROUND', (0, 1), (4, 1),color_head),
						('GRID',(0, 0), (-1, -1),  0.25, colors.black),
						('BOX', (0, 0), (-1, -1), 0.25, colors.black),
						('SPAN',(0,0),(4,0))
						]
		for elem in self.order_line:
			
			if elem.display_type in ['line_section','line_note']:
				data_content.append([Paragraph(elem.name,style_left_cell),'','','',''])
				array_style.append(('BACKGROUND', (0, x), (4, x),color_section))
				array_style.append(('SPAN',(0,x),(4,x)))
			else:
				data_content.append([])
				data_content[x].append(Paragraph(elem.product_id.default_code if elem.product_id.default_code else '',style_center_cell))
				data_content[x].append(Paragraph(elem.product_id.name if elem.product_id else '',style_left_cell))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.product_uom_qty)),style_center_cell))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.price_unit)),style_right_cell))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.price_subtotal)),style_right_cell))
			x+=1

		t4 = Table(data_content, colWidths=[2*cm,9.5*cm,2*cm,2*cm,4*cm],rowHeights=len(data_content)*[0.5*cm])

		t4.setStyle(TableStyle(array_style))

		elements.append(t4)

		data_subtotal = [['',Paragraph('SUB TOTAL',style_form),Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.amount_untaxed)),style_right)],
					['',Paragraph('IGV.18%',style_form),Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.amount_tax)),style_right)],
					['',Paragraph('TOTAL',style_form),Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.amount_total)),style_right)]]

		t5 = Table(data_subtotal, colWidths=[14.5*cm,2.5*cm,2.5*cm],rowHeights=len(data_subtotal)*[0.5*cm])
		t5.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP'),
								('BACKGROUND', (1, 0), (2, 2),color_subtotal),
								('GRID',(1, 0), (2, 2),  0.25, colors.black),
								('BOX', (1, 0), (2, 2), 0.25, colors.black),
								]))
		elements.append(t5)
		elements.append(Spacer(1, 12))

		data_acc = [[Paragraph(self._get_account_detraction(),style_form)],
					[Paragraph(self._get_account_cte(),style_form)]]

		t6 = Table(data_acc, colWidths=[19.5*cm],rowHeights=len(data_acc)*[0.5*cm])
		t6.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP'),
								('BACKGROUND', (0, 0), (-1, -1),color_section),
								('GRID',(0, 0), (-1, -1),  0.25, colors.black),
								('BOX', (0, 0), (-1, -1), 0.25, colors.black),
								]))

		elements.append(t6)
		elements.append(Spacer(1, 12))
		dat_term = [[self.note if self.note else '']]
		t_term = Table(dat_term, colWidths=[19.5*cm])
		t_term.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP')
								]))
		elements.append(t_term)
		elements.append(Spacer(1, 20))

		P = ReportBase.create_image(param_sale.presentation, direccion + 'presentation.jpg', 260.0, 100.0)
		data_footer = [[Paragraph('<font size=7.5>Atte.</font>',style_form),P if P else '','']]
		t7 = Table(data_footer, colWidths=[1*cm,10*cm,8.5*cm])
		t7.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
		elements.append(t7)

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('%s.pdf'%('Orden de Venta' if self.state == 'sale' else self.name),base64.encodestring(b''.join(f.readlines())))
