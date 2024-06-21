# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, ValidationError
import base64
import os

from reportlab.lib.units import inch,cm,mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
from odoo.modules.module import get_resource_path

class CostStructureIt(models.Model):
	_name = 'cost.structure.it'

	sale_order_id = fields.Many2one('sale.order',string='Pedido de Venta', required=False)
	name = fields.Char(string='Nombre',related='sale_order_id.name',readonly=True)
	partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
	date = fields.Date(string='Fecha')
	remuneration_line_ids = fields.One2many('cost.structure.remuneration','main_id',string=u'Remuneración')
	social_benefit_line_ids = fields.One2many('cost.structure.social.benefit','main_id',string=u'Beneficios Sociales')
	logistic_line_ids = fields.One2many('cost.structure.logistic','main_id',string=u'Logística')
	other_line_ids = fields.One2many('cost.structure.other','main_id',string=u'Otros')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)
	currency_id = fields.Many2one(string='Moneda', readonly=True, related='company_id.currency_id')

	def print_cost_structure(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file
		name_file = 'Estructura_Costos.pdf'
		doc = SimpleDocTemplate(direccion + name_file ,pagesize=A4, rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)
		elements = []

		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="Helvetica")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=6, leading=8, fontName="Helvetica")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=6, leading=8, fontName="Helvetica")

		head_table = []

		I = Image(os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'static','img','campomayor.png')),50,50)
		I2 = Image(os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'static','img','logo.png')),70,50)
		head_table.append([I if I else '',
							Paragraph('''<strong>ESTRUCTURA DE COSTOS</strong>''',style_title),
							I2 if I2 else ''
							])
		head_table.append([Paragraph('''<strong>NOMBRE O RAZON SOCIAL</strong>''',style_left),
							Paragraph(self.partner_id.name if self.partner_id else '',style_cell),
							''])
		head_table.append([Paragraph('''<strong>RUC</strong>''',style_left),
							Paragraph(self.partner_id.vat if self.partner_id.vat else '',style_cell),
							''])
		head_table.append([Paragraph('''<strong>SEDE</strong>''',style_left),
							Paragraph(self.partner_id.name if self.partner_id else '',style_cell),
							''])
		head_table.append([Paragraph(u'''<strong>DIRECCIÓN</strong>''',style_left),
							Paragraph(self.partner_id.street if self.partner_id.street else '',style_cell),
							''])
		head_table.append([Paragraph('''<strong>CONTACTO</strong>''',style_left),
							Paragraph(self.partner_id.mobile if self.partner_id.mobile else '',style_cell),
							''])
		head_table.append([Paragraph(u'''<strong>TELÉFONO DE CONTACTO</strong>''',style_left),
							Paragraph(self.partner_id.phone if self.partner_id.phone else '',style_cell),
							''])
		head_table.append([Paragraph('''<strong>FECHA</strong>''',style_left),
							Paragraph(self.date.strftime('%d/%m/%Y') if self.date else '',style_cell),
							''])
		head_table.append([Paragraph('''<strong>ESTRUCTURA DE COSTOS</strong>''',style_cell),'',''])

		table_head_table = Table(head_table, colWidths=[3.5*cm,12*cm,3.5*cm],rowHeights=[2*cm,0.5*cm,0.5*cm,0.5*cm,0.5*cm,0.5*cm,0.5*cm,0.5*cm,0.5*cm])
		color_cab = colors.Color(red=(185/255),green=(205/255),blue=(229/255))
		style_table = TableStyle([
				('BACKGROUND',(0,1),(0,7),color_cab),
				('SPAN',(1,1),(2,1)),
				('SPAN',(1,2),(2,2)),
				('SPAN',(1,3),(2,3)),
				('SPAN',(1,4),(2,4)),
				('SPAN',(1,5),(2,5)),
				('SPAN',(1,6),(2,6)),
				('SPAN',(1,7),(2,7)),
				('SPAN',(0,8),(2,8)),
				('BACKGROUND',(0,8),(2,8),color_cab),
				('VALIGN',(0,0),(2,7),'MIDDLE'),
				('ALIGN',(0,0),(2,0),'CENTER'),
				('GRID', (0,0), (-1,-1), 0.10, colors.black), 
				('BOX', (0,0), (-1,-1), 0.10, colors.black),
			])
		table_head_table.setStyle(style_table)
		elements.append(table_head_table)

		#-----------------------------------------------------------------------------------

		remuneration_table = []
		remuneration_table.append([Paragraph(u'''<strong>REMUNERACIÓN</strong>''',style_cell),'','',''])

		remuneration_table.append([Paragraph('''<strong>CONCEPTO</strong>''',style_cell),
							Paragraph('''<strong>COSTO UNITARIO</strong>''',style_cell),
							Paragraph('''<strong>CANTIDAD</strong>''',style_cell),
							Paragraph('''<strong>COSTO</strong>''',style_cell)])

		x=2
		total_rem = 0
		for fila in self.remuneration_line_ids:
			remuneration_table.append([])
			remuneration_table[x].append(Paragraph(fila.name if fila.name else '',style_left))
			remuneration_table[x].append(Paragraph('S/.'+str(fila.price_unit) if fila.price_unit else '',style_cell))
			remuneration_table[x].append(Paragraph(str(fila.quantity) if fila.quantity else '',style_cell))
			remuneration_table[x].append(Paragraph('S/.'+str(fila.subtotal) if fila.subtotal else '',style_cell))
			total_rem+=fila.subtotal
			x+=1

		table_remuneration_table = Table(remuneration_table, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(remuneration_table)*[0.5*cm])
		color_cab_rem = colors.Color(red=(195/255),green=(214/255),blue=(155/255))
		color_2_rem = colors.Color(red=(217/255),green=(217/255),blue=(217/255))
		style_table = TableStyle([
				('BACKGROUND',(0,0),(3,0),color_cab_rem),
				('BACKGROUND',(0,1),(3,1),color_2_rem),
				('SPAN',(0,0),(3,0)),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.10, colors.black), 
				('BOX', (0,0), (-1,-1), 0.10, colors.black),
			])
		table_remuneration_table.setStyle(style_table)
		elements.append(table_remuneration_table)

		remuneration_table_total = []
		remuneration_table_total.append(['','',Paragraph('''<strong>TOTAL REMUNERACIONES</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(total_rem,2))),style_cell)])

		table_remuneration_table_total = Table(remuneration_table_total, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(remuneration_table_total)*[0.5*cm])
		style_table = TableStyle([
				('BACKGROUND',(2,0),(2,0),color_2_rem),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (2,0), (3,0), 0.10, colors.black), 
				('BOX', (2,0), (3,0), 0.10, colors.black),
			])
		table_remuneration_table_total.setStyle(style_table)
		elements.append(table_remuneration_table_total)

		#-----------------------------------------------------------------------------------

		elements.append(Spacer(10, 10))

		social_benefit_table = []
		social_benefit_table.append([Paragraph(u'''<strong>BENEFICIOS SOCIALES</strong>''',style_cell),'','',''])

		social_benefit_table.append([Paragraph('''<strong>CONCEPTO</strong>''',style_cell),
							Paragraph('''<strong>% REMUNERACIÓN</strong>''',style_cell),
							'',
							Paragraph('''<strong>COSTO</strong>''',style_cell)])

		x=2
		total_social = 0
		for fila in self.social_benefit_line_ids:
			social_benefit_table.append([])
			social_benefit_table[x].append(Paragraph(fila.name if fila.name else '',style_left))
			social_benefit_table[x].append(Paragraph(str(fila.percentage)+'%' if fila.percentage else '',style_cell))
			social_benefit_table[x].append('')
			social_benefit_table[x].append(Paragraph('S/.'+str(fila.subtotal) if fila.subtotal else '',style_cell))
			total_social+=fila.subtotal
			x+=1

		table_social_benefit_table = Table(social_benefit_table, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(social_benefit_table)*[0.5*cm])
		style_table = TableStyle([
				('BACKGROUND',(0,0),(3,0),color_cab_rem),
				('BACKGROUND',(0,1),(3,1),color_2_rem),
				('SPAN',(0,0),(3,0)),
				('SPAN',(1,1),(2,1)),
				('SPAN',(1,2),(2,2)),
				('SPAN',(1,3),(2,3)),
				('SPAN',(1,4),(2,4)),
				('SPAN',(1,5),(2,5)),
				('SPAN',(1,6),(2,6)),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.10, colors.black), 
				('BOX', (0,0), (-1,-1), 0.10, colors.black),
			])
		table_social_benefit_table.setStyle(style_table)
		elements.append(table_social_benefit_table)

		social_benefit_table_total = []
		social_benefit_table_total.append(['','',Paragraph('''<strong>TOTAL BENEFICIOS SOCIALES</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(total_social,2))),style_cell)])

		table_social_benefit_table_total = Table(social_benefit_table_total, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(social_benefit_table_total)*[0.5*cm])
		style_table = TableStyle([
				('BACKGROUND',(2,0),(2,0),color_2_rem),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (2,0), (3,0), 0.10, colors.black), 
				('BOX', (2,0), (3,0), 0.10, colors.black),
			])
		table_social_benefit_table_total.setStyle(style_table)
		elements.append(table_social_benefit_table_total)

		#-----------------------------------------------------------------------------------

		elements.append(Spacer(10, 10))

		logistic_table = []
		logistic_table.append([Paragraph(u'''<strong>LOGÍSTICA</strong>''',style_cell),'','',''])

		logistic_table.append([Paragraph('''<strong>CONCEPTO</strong>''',style_cell),
							Paragraph('''<strong>COSTO UNITARIO</strong>''',style_cell),
							Paragraph('''<strong>CANTIDAD</strong>''',style_cell),
							Paragraph('''<strong>COSTO</strong>''',style_cell)])

		x=2
		total_logistic = 0
		for fila in self.logistic_line_ids:
			logistic_table.append([])
			logistic_table[x].append(Paragraph(fila.name if fila.name else '',style_left))
			logistic_table[x].append(Paragraph('S/.'+str(fila.price_unit) if fila.price_unit else '',style_cell))
			logistic_table[x].append(Paragraph(str(fila.quantity) if fila.quantity else '',style_cell))
			logistic_table[x].append(Paragraph('S/.'+str(fila.subtotal) if fila.subtotal else '',style_cell))
			total_logistic+=fila.subtotal
			x+=1

		table_logistic_table = Table(logistic_table, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(logistic_table)*[0.5*cm])
		style_table = TableStyle([
				('BACKGROUND',(0,0),(3,0),color_cab_rem),
				('BACKGROUND',(0,1),(3,1),color_2_rem),
				('SPAN',(0,0),(3,0)),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.10, colors.black), 
				('BOX', (0,0), (-1,-1), 0.10, colors.black),
			])
		table_logistic_table.setStyle(style_table)
		elements.append(table_logistic_table)

		logistic_table_total = []
		logistic_table_total.append(['','',Paragraph('''<strong>TOTAL LOGÍSTICA</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(total_logistic,2))),style_cell)])

		table_logistic_table_total = Table(logistic_table_total, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(logistic_table_total)*[0.5*cm])
		style_table = TableStyle([
				('BACKGROUND',(2,0),(2,0),color_2_rem),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (2,0), (3,0), 0.10, colors.black), 
				('BOX', (2,0), (3,0), 0.10, colors.black),
			])
		table_logistic_table_total.setStyle(style_table)
		elements.append(table_logistic_table_total)

		#-----------------------------------------------------------------------------------

		elements.append(Spacer(10, 10))

		other_table = []
		other_table.append([Paragraph(u'''<strong>OTROS</strong>''',style_cell),'','',''])

		other_table.append([Paragraph('''<strong>CONCEPTO</strong>''',style_cell),
							Paragraph('''<strong>COSTO UNITARIO</strong>''',style_cell),
							Paragraph('''<strong>CANTIDAD</strong>''',style_cell),
							Paragraph('''<strong>COSTO</strong>''',style_cell)])

		x=2
		total_other = 0
		for fila in self.other_line_ids:
			other_table.append([])
			other_table[x].append(Paragraph(fila.name if fila.name else '',style_left))
			other_table[x].append(Paragraph('S/.'+str(fila.price_unit) if fila.price_unit else '',style_cell))
			other_table[x].append(Paragraph(str(fila.quantity) if fila.quantity else '',style_cell))
			other_table[x].append(Paragraph('S/.'+str(fila.subtotal) if fila.subtotal else '',style_cell))
			total_other+=fila.subtotal
			x+=1

		table_other_table = Table(other_table, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(other_table)*[0.5*cm])

		style_table = TableStyle([
				('BACKGROUND',(0,0),(3,0),color_cab_rem),
				('BACKGROUND',(0,1),(3,1),color_2_rem),
				('SPAN',(0,0),(3,0)),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.10, colors.black), 
				('BOX', (0,0), (-1,-1), 0.10, colors.black),
			])
		table_other_table.setStyle(style_table)
		elements.append(table_other_table)

		logistic_table_total = []
		logistic_table_total.append(['','',Paragraph('''<strong>TOTAL OTROS</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(total_other,2))),style_cell)])

		table_other_table_total = Table(logistic_table_total, colWidths=[7*cm,4.1*cm,3.8*cm,4.1*cm],rowHeights=len(logistic_table_total)*[0.5*cm])
		style_table = TableStyle([
				('BACKGROUND',(2,0),(2,0),color_2_rem),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (2,0), (3,0), 0.10, colors.black), 
				('BOX', (2,0), (3,0), 0.10, colors.black),
			])
		table_other_table_total.setStyle(style_table)
		elements.append(table_other_table_total)

		#-----------------------------------------------------------------------------------

		elements.append(Spacer(20, 20))

		total_table = []

		total_total = total_rem + total_social + total_logistic + total_other

		total_table.append(['',Paragraph(u'''<strong>SUBTOTAL 1</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(total_total,2))),style_cell)])
		total_table.append(['',Paragraph(u'''<strong>GASTOS ADMINISTRATIVOS Y UTILIDADES     13% </strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(total_total*0.13,2))),style_cell)])
		total_table.append(['',Paragraph(u'''<strong>SUBTOTAL 2</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round((total_total*0.13)+total_total,2))),style_cell)])
		total_table.append(['',Paragraph(u'''<strong>I.G.V.     18%</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round(((total_total*0.13)+total_total)*0.18,2))),style_cell)])
		total_table.append(['',Paragraph(u'''<strong>TOTAL GENERAL</strong>''',style_cell),Paragraph('''<strong>S/.%s</strong>''' % (str(round((((total_total*0.13)+total_total)*0.18)+((total_total*0.13)+total_total),2))),style_cell)])

		table_total_table = Table(total_table, colWidths=[7*cm,7.9*cm,4.1*cm],rowHeights=len(total_table)*[0.5*cm])

		style_table = TableStyle([
				('BACKGROUND',(1,0),(1,3),color_2_rem),
				('BACKGROUND',(1,4),(1,4),color_cab),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (1,0), (2,4), 0.10, colors.black), 
				('BOX', (1,0), (2,4), 0.10, colors.black),
			])
		table_total_table.setStyle(style_table)
		elements.append(table_total_table)
		#-----------------------------------------------------------------------------------

		doc.build(elements)

		import importlib
		import sys
		importlib.reload(sys)

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Estructura de Costos.pdf',base64.encodestring(b''.join(f.readlines())))

class CostStructureRemuneration(models.Model):
	_name = 'cost.structure.remuneration'

	main_id = fields.Many2one('cost.structure.it',string='Estructura de Costos')
	currency_id = fields.Many2one(string='Moneda', readonly=True, related='main_id.currency_id')
	name = fields.Char(string='Concepto')
	price_unit = fields.Monetary(string='Costo Unitario',default=0)
	quantity = fields.Float(string='Cantidad',digits=(12,2),default=0)
	subtotal = fields.Monetary(string='Costo',compute='_calculate_subtotal')

	@api.depends('price_unit','quantity')
	def _calculate_subtotal(self):
		for i in self:
			i.subtotal = i.price_unit * i.quantity

class CostStructureSocialBenefit(models.Model):
	_name = 'cost.structure.social.benefit'

	main_id = fields.Many2one('cost.structure.it',string='Estructura de Costos')
	currency_id = fields.Many2one(string='Moneda', readonly=True, related='main_id.currency_id')
	name = fields.Char(string='Concepto')
	percentage = fields.Float(string=u'% Remuneración',digits=(12,2))
	subtotal = fields.Monetary(string='Costo')

class CostStructureLogistic(models.Model):
	_name = 'cost.structure.logistic'

	main_id = fields.Many2one('cost.structure.it',string='Estructura de Costos')
	currency_id = fields.Many2one(string='Moneda', readonly=True, related='main_id.currency_id')
	name = fields.Char(string='Concepto')
	price_unit = fields.Monetary(string='Costo Unitario',default=0)
	quantity = fields.Float(string='Cantidad',digits=(12,2),default=0)
	subtotal = fields.Monetary(string='Costo',compute='_calculate_subtotal')

	@api.depends('price_unit','quantity')
	def _calculate_subtotal(self):
		for i in self:
			i.subtotal = i.price_unit * i.quantity

class CostStructureOther(models.Model):
	_name = 'cost.structure.other'

	main_id = fields.Many2one('cost.structure.it',string='Estructura de Costos')
	currency_id = fields.Many2one(string='Moneda', readonly=True, related='main_id.currency_id')
	name = fields.Char(string='Concepto')
	price_unit = fields.Monetary(string='Costo Unitario',default=0)
	quantity = fields.Float(string='Cantidad',digits=(12,2),default=0)
	subtotal = fields.Monetary(string='Costo',compute='_calculate_subtotal')

	@api.depends('price_unit','quantity')
	def _calculate_subtotal(self):
		for i in self:
			i.subtotal = i.price_unit * i.quantity