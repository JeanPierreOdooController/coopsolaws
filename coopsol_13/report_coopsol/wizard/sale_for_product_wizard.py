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
import time

class SaleForProductWizard(models.TransientModel):
	_name = 'sale.for.product.wizard'

	name = fields.Char()
	product_id = fields.Many2one('product.product',string='Producto')
	date = fields.Date(string='Fecha',default=fields.Date.context_today)
	partner_id = fields.Many2one('res.partner',string='Cliente')
	contact_id = fields.Many2one('res.partner',string='Contacto')
	address = fields.Char(string=u'Lugar de Cotización')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def do_report(self):
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = u"Cotización - %s.pdf" % (self.product_id.name.replace('/',''))

		archivo_pdf = SimpleDocTemplate(direccion + name_file, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)

		elements = []
		#Estilos 
		style_title = ParagraphStyle(name = 'Center',alignment = TA_JUSTIFY, fontSize = 13, fontName="Helvetica-Bold" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 10, fontName="Helvetica" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=12, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=10, fontName="Helvetica")
		style_center = ParagraphStyle(name = 'Center', alignment=TA_CENTER, fontSize=10, fontName="Helvetica")

		company = self.company_id

		I = ReportBase.create_image(company.logo, direccion + 'logo.jpg', 180.0, 35.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(Spacer(10, 20))

		texto = self.address + ', ' + str(self.date.day) + ' de ' + self.get_month_name(self.date.month) + ' de ' + str(self.date.year)
		elements.append(Paragraph('<strong><em>%s</em></strong>' % (texto), style_right))
		elements.append(Spacer(1, 25))
		elements.append(Paragraph('<strong><em>Señores:</em></strong>', style_form))
		elements.append(Spacer(1, 5))
		elements.append(Paragraph('<strong>%s</strong>' % (self.partner_id.name), style_form))
		elements.append(Spacer(1, 7))
		elements.append(Paragraph('<strong><em>Atención</em></strong>', style_form))
		elements.append(Spacer(1, 5))
		elements.append(Paragraph('<strong>%s</strong>'%(self.contact_id.name), style_form))
		elements.append(Spacer(1, 5))
		elements.append(Paragraph('<strong>%s</strong>'%(self.contact_id.function if self.contact_id.function else ''), style_form))
		elements.append(Spacer(1, 20))

		elements.append(Paragraph(u'Por medio de la presente le hacemos llegar nuestra cotización por una máquina para mantenimiento de pisos.', style_form))
		elements.append(Spacer(1, 20))

		elements.append(Paragraph(self.product_id.name.upper(), style_title))
		elements.append(Spacer(1, 12))
		styleSheet = getSampleStyleSheet()
		param_sale = self.env['main.parameter.sale'].search([('company_id','=',self.company_id.id)])
		P = ReportBase.create_image(self.product_id.image_1920, direccion + 'product.jpg', param_sale.width_product, param_sale.height_product)
		data_content = []
		x = 0
		for elem in self.product_id.characteristic_line_ids:
			data_content.append([])
			data_content[x].append(Paragraph(u'<font size=8>•\t%s</font>'%(elem.description),styleSheet["BodyText"]))
			if x == 0:
				data_content[x].append(P if P else '')
			else:
				data_content[x].append('')
			x += 1
		if x < 10:
			for i in range(1,10-x):
				data_content.append(['',''])
				x += 1
		data_content.append([Paragraph('<strong>Precio: S/.%s + IGV</strong>'%('{:,.2f}'.format(decimal.Decimal ("%0.2f" % self.product_id.lst_price))),style_left),''])

		t2 = Table(data_content, colWidths=[10*cm,9*cm])
		t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
							   ('SPAN',(1, 0),(1, x)),
							   ]))
		elements.append(t2)
		elements.append(Spacer(1, 12))

		elements.append(Paragraph(u'<strong>Plazo de Entrega:</strong> Inmediata', style_form))
		elements.append(Spacer(1, 5))
		elements.append(Paragraph(u'<strong>Garantía:</strong> Un año', style_form))
		elements.append(Spacer(1, 12))
		elements.append(Paragraph(u'<em>Quedamos a sus órdenes para cualquier consulta o comentario al respecto.</em> Un año', style_form))
		elements.append(Spacer(1, 20))
		data_footer = [[Paragraph('<strong><em>%s</em></strong>'%(param_sale.quotation_manager if param_sale.quotation_manager else ''),style_center),''],
						[Paragraph('<strong><em>%s</em></strong>'%(param_sale.function_manager if param_sale.function_manager else ''),style_center),''],
						[Paragraph('<font color=#22ba74><strong><em>%s</em></strong></font>'%(company.name if company.name else ''),style_center),''],
						[Paragraph('<font color=red><strong><em>%s</em></strong></font>'%(company.slogan if company.slogan else ''),style_center),''],
						[Paragraph('<font color=blue><strong><em><u>%s</u></em></strong></font>'%(company.website if company.website else ''),style_center),'']]
		t3 = Table(data_footer, colWidths=[7.5*cm,12*cm])
		t3.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
							   ]))
		elements.append(Spacer(1, 12))
		elements.append(t3)
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
