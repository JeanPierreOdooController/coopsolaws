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

class PurchaseOrderPrintWizard(models.TransientModel):
	_name = 'purchase.order.print.wizard'

	name = fields.Char()
	purchase_id = fields.Many2one('purchase.order',string='Compra')
	type = fields.Selection([('local','Local'),('ext','Exterior')], default='local')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)


	def do_report(self):
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Orden de Compra.pdf"

		archivo_pdf = SimpleDocTemplate(direccion + name_file, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)

		elements = []
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 15, fontName="Helvetica-Bold" )

		company = self.company_id

		if self.type == 'local':
			#Estilos 
			style_subtitle = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 12, fontName="Helvetica-Bold" )
			style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 8, fontName="Helvetica" )
			style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=8, fontName="Helvetica")
			style_cell = ParagraphStyle(name = 'Center', alignment=TA_CENTER, fontSize=8, fontName="Helvetica")

			elements.append(Paragraph(u'ORDEN DE COMPRA LOCAL', style_title))
			elements.append(Spacer(1, 12))
			elements.append(Paragraph(u'OCL # %s'%(self.purchase_id.name), style_subtitle))
			elements.append(Spacer(1, 20))
			date = self.purchase_id.date_order
			elements.append(Paragraph(u'%s de %s de %s'%(str(date.day),
														self.get_month_name(date.month),
														str(date.year)), style_right))
			elements.append(Spacer(1, 12))
			data_header = [['Sr(es): ',Paragraph(self.purchase_id.partner_id.name,style_form),'Entrega:',''],
							['',Paragraph(self.purchase_id.partner_id.street if self.purchase_id.partner_id.street else '',style_form),'Fecha de Entrega:',''],
							['RUC:',self.purchase_id.partner_id.vat if self.purchase_id.partner_id.vat else '','Cotización Nro:',self.purchase_id.quot_number if self.purchase_id.quot_number else ''],
							['Telefono:',company.partner_id.phone if company.partner_id.phone else '','Solicitudes:',''],
							['Contacto:',self.purchase_id.contact_id.name if self.purchase_id.contact_id else '','C. Costo:',self.purchase_id.analytic_account_id.name if self.purchase_id.analytic_account_id else ''],
							[u'Condición de Pago: %s'%(self.purchase_id.payment_term_id.name if self.purchase_id.payment_term_id else '')]]
			
			
			t = Table(data_header, colWidths=[2*cm,9*cm,3.2*cm,4.8*cm])
			t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP')
								]))

			elements.append(t)

			elements.append(Spacer(1, 12))

			data_content = [[Paragraph('<b>Itm</b>',style_cell),Paragraph('<b>Código</b>',style_cell),Paragraph('<b>Cantidad</b>',style_right),Paragraph('<b>Uni</b>',style_cell),
			Paragraph('<b>Descripcion</b>',style_form),Paragraph('<b>Precio</b>',style_right),Paragraph('<b>Total</b>',style_right)]]
			x = 1
			for elem in self.purchase_id.order_line:
				data_content.append([])
				data_content[x].append(Paragraph(str(x),style_cell))
				data_content[x].append(Paragraph(elem.product_id.default_code if elem.product_id.default_code else '',style_cell))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.product_qty)),style_right))
				data_content[x].append(Paragraph(elem.product_uom.name if elem.product_uom else '',style_cell))
				data_content[x].append(Paragraph(elem.product_id.name if elem.product_id else '',style_form))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.price_unit)),style_right))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.price_subtotal)),style_right))
				x+=1

			t2 = Table(data_content, colWidths=[1*cm,2.5*cm,2.2*cm,1.9*cm,7*cm,2*cm,2.5*cm])

			t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP'),
									('BOX', (0,0), (6,0), 0.25, colors.black)
								]))

			elements.append(t2)

			elements.append(Spacer(1, 12))

			elements.append(Paragraph(u'------------------', style_right))
			data_subtotal = [[Paragraph('<b>Sub Total:</b>',style_right),Paragraph('<b>%s</b>'%('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.purchase_id.amount_untaxed))),style_right)],
							[Paragraph('<b>Impuesto:</b>',style_right),Paragraph('<b>%s</b>'%('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.purchase_id.amount_tax))),style_right)]]

			t3 = Table(data_subtotal, colWidths=[16.6*cm,2.5*cm])

			t3.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP')
								]))

			elements.append(t3)
			elements.append(Paragraph(u'------------------', style_right))

			data_total = [[Paragraph('<b>Total: %s</b>'%(self.purchase_id.currency_id.symbol if self.purchase_id.currency_id else ''),style_right),Paragraph('<b>%s</b>'%('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.purchase_id.amount_total))),style_right)]]

			t4 = Table(data_total, colWidths=[16.6*cm,2.5*cm])

			t4.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP')
								]))

			elements.append(t4)
			elements.append(Spacer(1, 12))

			d = Drawing(550, 1)
			d.add(Line(0, 0, 550, 0))
			elements.append(d)
			elements.append(Spacer(1, 5))
			data_footer = [['ENTREGAR EN:',Paragraph(self.purchase_id.picking_type_id.warehouse_id.partner_id.street if self.purchase_id.picking_type_id.warehouse_id.partner_id.street else '',style_form)],
							['OBSERVACIONES:',Paragraph(self.purchase_id.obs if self.purchase_id.obs else '',style_form)]]
			
			t5 = Table(data_footer, colWidths=[4*cm,15*cm])
			t5.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP')
								]))
			elements.append(t5)
			elements.append(Spacer(1, 5))
			elements.append(d)
			elements.append(Spacer(1, 5))
			elements.append(Paragraph('NOTA: %s'%(self.purchase_id.notes if self.purchase_id.notes else ''),style_form))
			elements.append(Spacer(1, 3))
			elements.append(Paragraph('Facturar a: %s'%(company.name),style_form))
			elements.append(Spacer(1, 3))
			elements.append(Paragraph('Direcc: %s'%(company.street if company.street else ''),style_form))
			elements.append(Spacer(1, 5))
			elements.append(Paragraph('Horario de Recepción:',style_form))
			elements.append(Spacer(1, 50))

			d = Drawing(550, 1)
			d.add(Line(75, 0, 200, 0))
			d.add(Line(340, 0, 465, 0))
			elements.append(d)

			data_signature = [[Paragraph('Oficina de Compras',style_cell),Paragraph('Autorizado Por',style_cell)]]
			t6 = Table(data_signature, colWidths=[9.5	*cm,9.5*cm])

			t6.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP')
								]))

			elements.append(t6)

		else:
			style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 7, fontName="Helvetica", leading=8)
			style_cell = ParagraphStyle(name = 'Center', alignment=TA_CENTER, fontSize=7, fontName="Helvetica")
			style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=7, fontName="Helvetica")

			I = None #ReportBase.create_image(company.logo, direccion + 'logo.jpg', 180.0, 35.0)
			data = [[I if I else '']]
			ti = Table(data, [20 * cm])
			ti.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
			elements.append(ti)
			elements.append(Spacer(10, 20))

			elements.append(Paragraph(u'ORDEN DE COMPRA', style_title))
			elements.append(Spacer(1, 20))
			data_header = [[Paragraph('<font color=#284466><b>%s</b></font>'%(company.name),style_form),'','',''],
			[Paragraph('%s - %s'%(company.state_id.name if company.state_id else '',company.country_id.name if company.country_id else ''),style_form),'',Paragraph('<font color=red><strong>Ship To:</strong></font>',style_form),Paragraph(self.purchase_id.ambassador_id.ship_to if self.purchase_id.ambassador_id.ship_to else '',style_form)],
			[Paragraph(company.street if company.street else '',style_form),'','',''],
			['','','',''],['','','',''],
			[Paragraph(u'Número de Orden:',style_form),Paragraph(self.purchase_id.name,style_form),'',''],
			[Paragraph('Fecha:',style_form),Paragraph(self.purchase_id.date_order.strftime('%d-%m-%Y'),style_form),'',''],
			[Paragraph(u'Contacto:',style_form),Paragraph(self.purchase_id.contact_id.name if self.purchase_id.contact_id else '',style_form),'',''],
			[Paragraph('Email:',style_form),Paragraph('<font color=blue><strong><em><u>%s</u></em></strong></font>'%(self.purchase_id.contact_id.email if self.purchase_id.contact_id.email else ''),style_form),'',''],
			['','','',''],
			[Paragraph('<b>PROVEEDOR</b>',style_form),'','',''],
			[Paragraph('<b>%s</b>'%(self.purchase_id.partner_id.name if self.purchase_id.partner_id else ''),style_form),'','',''],
			[Paragraph(self.purchase_id.partner_id.street if self.purchase_id.partner_id.street else '',style_form),'','',''],
			['','','',''],
			[Paragraph('<b>CONTACTO:</b>',style_form),Paragraph('<b>%s</b>'%(self.purchase_id.contact_partner_id.name if self.purchase_id.contact_partner_id else ''),style_form),'','']]
			
			
			t = Table(data_header, colWidths=[3*cm,8*cm,1.5*cm,6.5*cm],rowHeights=len(data_header)*[0.3*cm])
			t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP'),
								('SPAN',(0,0),(1,0)),
								('SPAN',(0,1),(1,1)),
								('SPAN',(0,2),(1,3)),
								('SPAN',(0,11),(1,11)),
								('SPAN',(0,12),(1,13)),
								('SPAN',(3,1),(3,9))
								]))

			elements.append(t)
			elements.append(Spacer(1, 12))

			elements.append(Paragraph('    Por medio de la presente les solicitamos se sirvan atendernos con lo siguiente:',style_form))
			elements.append(Spacer(1, 12))

			data_content = [[Paragraph(u'<b>Código</b>',style_cell),Paragraph(u'<b>Descripción</b>',style_cell),Paragraph(u'<b>Uni</b>',style_cell),
			Paragraph(u'<b>Cantidad</b>',style_cell),Paragraph(u'<b>P. Unitario</b>',style_cell),Paragraph(u'<b>TOTAL</b>',style_cell)]]
			x = 1
			for elem in self.purchase_id.order_line:
				data_content.append([])
				data_content[x].append(Paragraph(elem.product_id.default_code if elem.product_id.default_code else '',style_cell))
				data_content[x].append(Paragraph(elem.product_id.name if elem.product_id else '',style_form))
				data_content[x].append(Paragraph(elem.product_uom.name if elem.product_uom else '',style_cell))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.product_qty)),style_right))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.price_unit)),style_right))
				data_content[x].append(Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % elem.price_subtotal)),style_right))
				x+=1
			
			data_content.append(['','','','','',Paragraph('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.purchase_id.amount_untaxed)),style_right)])

			t2 = Table(data_content, colWidths=[1.5*cm,9*cm,2*cm,2*cm,2*cm,2.5*cm])

			color_cab = colors.Color(red=(0/255),green=(176/255),blue=(240/255))

			t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
								('VALIGN', (0, 0), (-1, -1), 'TOP'),
								('BACKGROUND', (0, 0), (5, 0),color_cab),
								('BOX', (0, 0), (5, x-1), 0.25, colors.black),
								('GRID',(0,0),(5,x-1),  0.25, colors.black),
								('BOX', (5, x), (5, x), 0.25, colors.black)
								]))

			elements.append(t2)

			elements.append(Spacer(1, 12))

			elements.append(Paragraph(u'<b>COMPRADOR: %s</b>'%(self.purchase_id.user_id.name if self.purchase_id.user_id else u'Jesús E. Garcia Grandjean'),style_form))

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(name_file,base64.encodestring(b''.join(f.readlines())))

	def get_month_name(self, month):
		array = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
				 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
		return array[month - 1]