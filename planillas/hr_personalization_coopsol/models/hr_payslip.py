# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from math import modf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,letter, inch, landscape
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import subprocess
import sys
from datetime import *

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from PyPDF2 import PdfFileReader, PdfFileWriter
except:
	install('PyPDF2')

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def _get_sql_wd(self,code_unico):
		struct_id = self.payslip_run_id.slip_ids[0].struct_id.id
		sql = """
	select T.*
		from (SELECT	
			he.id as employee_id,
			he.identification_id,
			he.name,
			hc.id as contract_id,
			case when hpwdt.code in ('DLAB','DLABN') then 'BAS' else hpwdt.code end as code,
			hpwdt.id as wd_type_id,
			sum(hpwd.number_of_days) as wd_total_dias,
			sum(hpwd.number_of_hours) as wd_total_horas
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id 
			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_payslip_worked_days hpwd on hpwd.payslip_id=hp.id
			left join hr_payslip_worked_days_type hpwdt on hpwdt.id=hpwd.wd_type_id
			where hp.id = {slip}
			and hp.company_id = {company}
			and hp.struct_id = {struct_id}
			and(hpwd.number_of_days <> 0 or hpwd.number_of_hours <> 0)
			group by he.id,he.identification_id,hc.id,hpwdt.code,hpwdt.id
			order by he.identification_id)T
		where T.code = '{code}'
			""" .format(
				slip = self.id,
				company = self.company_id.id,
				struct_id = struct_id,
				code = code_unico
			)
		return sql

	def generate_voucher_v2(self, objeto_canvas):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		EXT = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_ext.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DLAB = self.get_dlabs()
		# print("DLAB",DLAB)
		DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)
		EXT_DEC_INT = modf(sum(EXT.mapped('number_of_hours')))
		DLAB = DLAB + self.holidays
		DIAS_FAL = sum(DNLAB.mapped('number_of_days'))
		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))
		DIAS_NLAB = DIAS_FAL + DIA_VAC + DIA_SUB

		if DIA_SUB == 30:
			DIA_SUB = self.date_to.day
			DLAB = 0
			DIAS_NLAB = DIA_VAC + DIA_SUB
		elif DIA_VAC == 30:
			DIA_VAC = self.date_to.day
			DLAB = 0
			DIAS_NLAB = DIA_VAC + DIA_SUB
		elif (DIA_SUB + DIA_VAC) == 30:
			DIAS_NLAB = self.date_to.day
			DLAB = 0

		#### SALARY RULE CATEGORIES ####
		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids)
		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)

		if not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=8, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		internal_width = [2.5 * cm]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(10, 20)

		width, height = A4  # 595 , 842
		wReal = width - 15
		hReal = height - 40
		pagina = 1
		size_widths = [7, 110, 50]

		if Contract.situation_id.name == 'BAJA':
			if self.date_from <= Contract.date_end <= self.date_to:
				date_end = Contract.date_end
			else:
				date_end = False
		else:
			date_end = False

		# PRIMERA COPIA BOLETA DE PAGO
		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 45.0)
		data = [
			[Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left), I if I else ''],
			[Paragraph('%s' % self.company_id.street_name or '', style_left), ''],
			[Paragraph('RUC N° %s' % self.company_id.vat or '', style_left), ''],
		]
		t = Table(data, [16 * cm, 4 * cm], len(data) * [0.4 * cm])
		t.setStyle(TableStyle([
			('SPAN', (1, 0), (1, -1)),
			# ('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#B0B0B0")),
			# ('BOX', (2, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 15)

		objeto_canvas.setFont("Helvetica-Bold", 11)
		objeto_canvas.setFillColor(colors.black)
		objeto_canvas.drawCentredString((wReal / 2) + 20, hReal - 30, "BOLETA DE REMUNERACIONES")
		objeto_canvas.setFont("Helvetica-Bold", 10)
		objeto_canvas.drawCentredString((wReal / 2) + 20, hReal - 42, "PLANILLA %s" % self.payslip_run_id.name or '')

		objeto_canvas.setFont("Helvetica", 10)
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment = 1

		data = [
			[Paragraph(
				'<strong>__________________________________________________________________________________________________________________</strong>',
				style_left)]
		]
		t = Table(data, [20 * cm], len(data) * [0.12 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 45)

		dias_vaca = 0
		fecha_ing_vac = fecha_fin_vac = ''
		if len(self.accrual_vacation_ids) > 0:
			estado_vaca = 'SI'
			for vacaciones in self.accrual_vacation_ids:
				dias_vaca += vacaciones.days
				fecha_ing_vac = vacaciones.request_date_from
				fecha_fin_vac = vacaciones.request_date_to
		else:
			estado_vaca = 'NO'

		data = [
			[Paragraph('<strong>Trabajador</strong>', style_left), Paragraph(': %s' % Employee.name.title() or '', style_left),
			 Paragraph('<strong>Fecha de Ingreso</strong>', style_left), Paragraph(': %s' % str(datetime.strftime((admission_date), '%d-%m-%Y')) or '', style_left),
			 Paragraph('<strong>Dias Lab</strong>', style_left), Paragraph(': %d' % DLAB or '', style_left)],
			[Paragraph('<strong>Tipo Trab</strong>', style_left), Paragraph(': %s' % Contract.worker_type_id.name.capitalize() if Contract.worker_type_id.name else '', style_left),
			 Paragraph('<strong>Fecha de Cese</strong>', style_left), Paragraph(': %s' % datetime.strftime(date_end, '%d-%m-%Y') if date_end else '', style_left),
			 Paragraph('<strong>Dias Subs</strong>', style_left), Paragraph(': %d' % DIA_SUB or '0', style_left)],
			[Paragraph('<strong>Area</strong>', style_left), Paragraph(': %s' % Contract.department_id.name.capitalize() if Contract.department_id.name else '', style_left),
			 Paragraph('<strong>Periodo Vacac</strong>', style_left), Paragraph(': %s' % estado_vaca or '', style_left),
			 Paragraph('<strong>Dias No Lab</strong>', style_left), Paragraph(': %d' % DIAS_NLAB or '0', style_left)],
			[Paragraph('<strong>Cargo</strong>', style_left), Paragraph(': %s' % Contract.job_id.name.capitalize() if Contract.job_id.name else '', style_left),
			 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Inicio Vac</strong>', style_left), Paragraph(': %s' % datetime.strftime((fecha_ing_vac), '%d-%m-%Y') if fecha_ing_vac != '' else '', style_left),
			 Paragraph('<strong>Dias Vac</strong>', style_left), Paragraph(': %d' % dias_vaca or '0', style_left)],
			[Paragraph('<strong>Centro de Costos</strong>', style_left), Paragraph(': %s' % self.distribution_id.description.capitalize() if self.distribution_id.description else self.distribution_id.name, style_left),
			 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Fin Vac</strong>', style_left), Paragraph(': %s' % datetime.strftime((fecha_fin_vac), '%d-%m-%Y') if fecha_fin_vac != '' else '', style_left),
			 Paragraph('<strong>N° Horas Ord</strong>', style_left), Paragraph(': %s' % str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_left)],
			[Paragraph('<strong>Tipo de Docum</strong>', style_left), Paragraph(': %s <strong>Nro.</strong> %s' % (Employee.type_document_id.name or '', Employee.identification_id or ''), style_left),
			 Paragraph('<strong>Reg Pensionario</strong>', style_left), Paragraph(': %s' % self.membership_id.name.title() if self.membership_id.name else Contract.membership_id.name,	style_left),
			 Paragraph('<strong>N° Horas Ext</strong>', style_left), Paragraph(': %s' % str(ReportBase.custom_round(EXT_DEC_INT[1])) or '', style_left)],
			[Paragraph('<strong>Regimen Laboral</strong>', style_left), Paragraph(': %s' % dict(self._fields['labor_regime'].selection).get(self.labor_regime) or '', style_left),
			 Paragraph('<strong>C.U.S.P.P.</strong>', style_left), Paragraph(': %s' % Contract.cuspp if Contract.cuspp else '', style_left),
			 Paragraph('<strong>Rem Basica</strong>', style_left), Paragraph(': {:,.2f}'.format(self.wage) or '0.00', style_left)],
		]
		t = Table(data, [3 * cm, 6 * cm, 3 * cm, 3 * cm, 3 * cm, 2 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 135)

		data = [[
			Paragraph('<strong>INGRESOS</strong>', style_cell),
			Paragraph('<strong>DESCUENTOS</strong>', style_cell),
			Paragraph('<strong>APORTES EMPLEADOR</strong>', style_cell)
		]]
		t = Table(data, [8 * cm, 7 * cm, 5 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 160)

		def particionar_text(c, tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet, 'Helvetica', 8, tam)
				if len(lines) > 1:
					return tet[:-1]
			return tet

		def verify_linea(self, c, wReal, hReal, posactual, valor, pagina, size_widths):
			if posactual < 50:
				c.showPage()
				return pagina + 1, hReal - 142
			else:
				return pagina, posactual - valor

		h_ing = h_des = h_apor = hReal - 170
		total_ing = total_des = total_apor = 0
		for ingreso in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 43

			self.env.cr.execute(self._get_sql_wd(ingreso.code))
			res_wds = self.env.cr.dictfetchall()
			# print("res_wds",res_wds)
			# print("ingreso.employee_id.name",ingreso.employee_id.name)
			if len(res_wds)>0:
				if ingreso.code == res_wds[0]['code']:
					objeto_canvas.drawRightString(first_pos, h_ing,'{:,.2f}'.format(res_wds[0]['wd_total_dias']) if res_wds[0]['wd_total_dias']>0 else '{:,.2f}'.format(res_wds[0]['wd_total_horas']))
			first_pos += size_widths[0]
			objeto_canvas.drawString(first_pos, h_ing, particionar_text(ingreso.name if ingreso.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 80, h_ing,'{:,.2f}'.format(ingreso.total) if ingreso.total else '0.00')
			first_pos += size_widths[2]

			total_ing += ingreso.total
			pagina, h_ing = verify_linea(self, objeto_canvas, wReal, hReal, h_ing, 12, pagina, size_widths)

		for descuento in CONTRIBUTIONS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 248
			objeto_canvas.drawString(first_pos, h_des, particionar_text(descuento.name if descuento.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 80, h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[2]

			total_des += descuento.total
			pagina, h_des = verify_linea(self, objeto_canvas, wReal, hReal, h_des, 12, pagina, size_widths)

		for descuento in DISCOUNTS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 248
			objeto_canvas.drawString(first_pos, h_des, particionar_text(descuento.name if descuento.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 80, h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[2]

			total_des += descuento.total
			pagina, h_des = verify_linea(self, objeto_canvas, wReal, hReal, h_des, 12, pagina, size_widths)

		for aporte in CONTRIBUTIONS_EMP:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 447
			objeto_canvas.drawString(first_pos, h_apor, particionar_text(aporte.name if aporte.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 25, h_apor,'{:,.2f}'.format(aporte.total) if aporte.total else '0.00')
			first_pos += size_widths[2]

			total_apor += aporte.total
			pagina, h_apor = verify_linea(self, objeto_canvas, wReal, hReal, h_apor, 12, pagina, size_widths)

		data = [[
			Paragraph('TOTAL INGRESOS S/', style_title),
			Paragraph('<strong>{:,.2f}</strong>'.format(total_ing) or '0.00', style_right),
			Paragraph('TOTAL DESCUENTOS S/', style_title),
			Paragraph('<strong>{:,.2f}</strong>'.format(total_des) or '0.00', style_right),
			Paragraph('TOTAL APORTES S/', style_title),
			Paragraph('<strong>{:,.2f}</strong>'.format(total_apor) or '0.00', style_right)
		]]
		t = Table(data, [6 * cm, 2 * cm, 5 * cm, 2 * cm, 3 * cm, 2 * cm, ], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (1, -1), 0.25, colors.black),
			('BOX', (2, 0), (3, -1), 0.25, colors.black),
			('BOX', (4, 0), (5, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 290)

		data = [['',
				 Paragraph('<strong>NETO A PAGAR S/</strong>', style_cell),
				 Paragraph('<strong>{:,.2f}</strong>'.format(NET_TO_PAY.total) or '0.00', style_cell), ''
				 ]]
		t = Table(data, [7 * cm, 4 * cm, 3 * cm, 6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (1, 0), (2, -1), 0.25, colors.black),
			('BOX', (1, 0), (2, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 315)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		data = [
			[I if I else '', ''],
			[Paragraph('<strong>__________________________</strong>', style_title),
			 Paragraph('<strong>__________________________</strong>', style_title)],
			[Paragraph('<strong>EMPLEADOR</strong>', style_title),
			 Paragraph('<strong>RECIBI CONFORME <br/> TRABAJADOR</strong>', style_title)]
		]
		t = Table(data, [10 * cm, 10 * cm], 3 * [0.5 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 380)

		# SEGUNDA COPIA BOLETA DE PAGO
		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 45.0)
		data = [
			[Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left), I if I else ''],
			[Paragraph('%s' % self.company_id.street_name or '', style_left), ''],
			[Paragraph('RUC N° %s' % self.company_id.vat or '', style_left), ''],
		]
		t = Table(data, [16 * cm, 4 * cm], len(data) * [0.4 * cm])
		t.setStyle(TableStyle([
			('SPAN', (1, 0), (1, -1)),
			# ('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#B0B0B0")),
			# ('BOX', (2, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 430)

		objeto_canvas.setFont("Helvetica-Bold", 11)
		objeto_canvas.setFillColor(colors.black)
		objeto_canvas.drawCentredString((wReal / 2) + 20, hReal - 445, "BOLETA DE REMUNERACIONES")
		objeto_canvas.setFont("Helvetica-Bold", 10)
		objeto_canvas.drawCentredString((wReal / 2) + 20, hReal - 457, "PLANILLA %s" % self.payslip_run_id.name or '')

		objeto_canvas.setFont("Helvetica", 10)
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment = 1

		data = [
			[Paragraph(
				'<strong>__________________________________________________________________________________________________________________</strong>',
				style_left)]
		]
		t = Table(data, [20 * cm], len(data) * [0.12 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 460)

		data = [
			[Paragraph('<strong>Trabajador</strong>', style_left), Paragraph(': %s' % Employee.name.title() or '', style_left),
			 Paragraph('<strong>Fecha de Ingreso</strong>', style_left), Paragraph(': %s' % str(datetime.strftime((admission_date), '%d-%m-%Y')) or '', style_left),
			 Paragraph('<strong>Dias Lab</strong>', style_left), Paragraph(': %d' % DLAB or '', style_left)],
			[Paragraph('<strong>Tipo Trab</strong>', style_left), Paragraph(': %s' % Contract.worker_type_id.name.capitalize() if Contract.worker_type_id.name else '', style_left),
			 Paragraph('<strong>Fecha de Cese</strong>', style_left), Paragraph(': %s' % datetime.strftime(date_end, '%d-%m-%Y') if date_end else '', style_left),
			 Paragraph('<strong>Dias Subs</strong>', style_left), Paragraph(': %d' % DIA_SUB or '0', style_left)],
			[Paragraph('<strong>Area</strong>', style_left), Paragraph(': %s' % Contract.department_id.name.capitalize() if Contract.department_id.name else '', style_left),
			 Paragraph('<strong>Periodo Vacac</strong>', style_left), Paragraph(': %s' % estado_vaca or '', style_left),
			 Paragraph('<strong>Dias No Lab</strong>', style_left), Paragraph(': %d' % DIAS_NLAB or '0', style_left)],
			[Paragraph('<strong>Cargo</strong>', style_left), Paragraph(': %s' % Contract.job_id.name.capitalize() if Contract.job_id.name else '', style_left),
			 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Inicio Vac</strong>', style_left), Paragraph(': %s' % datetime.strftime((fecha_ing_vac), '%d-%m-%Y') if fecha_ing_vac != '' else '', style_left),
			 Paragraph('<strong>Dias Vac</strong>', style_left), Paragraph(': %d' % dias_vaca or '0', style_left)],
			[Paragraph('<strong>Centro de Costos</strong>', style_left), Paragraph(': %s' % self.distribution_id.description.capitalize() if self.distribution_id.description else self.distribution_id.name, style_left),
			 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Fin Vac</strong>', style_left), Paragraph(': %s' % datetime.strftime((fecha_fin_vac), '%d-%m-%Y') if fecha_fin_vac != '' else '', style_left),
			 Paragraph('<strong>N° Horas Ord</strong>', style_left), Paragraph(': %s' % str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_left)],
			[Paragraph('<strong>Tipo de Docum</strong>', style_left), Paragraph(': %s <strong>Nro.</strong> %s' % (Employee.type_document_id.name or '', Employee.identification_id or ''), style_left),
			 Paragraph('<strong>Reg Pensionario</strong>', style_left), Paragraph(': %s' % self.membership_id.name.title() if self.membership_id.name else Contract.membership_id.name,	style_left),
			 Paragraph('<strong>N° Horas Ext</strong>', style_left), Paragraph(': %s' % str(ReportBase.custom_round(EXT_DEC_INT[1])) or '', style_left)],
			[Paragraph('<strong>Regimen Laboral</strong>', style_left), Paragraph(': %s' % dict(self._fields['labor_regime'].selection).get(self.labor_regime) or '', style_left),
			 Paragraph('<strong>C.U.S.P.P.</strong>', style_left), Paragraph(': %s' % Contract.cuspp if Contract.cuspp else '', style_left),
			 Paragraph('<strong>Rem Basica</strong>', style_left), Paragraph(': {:,.2f}'.format(self.wage) or '0.00', style_left)],
		]
		t = Table(data, [3 * cm, 6 * cm, 3 * cm, 3 * cm, 3 * cm, 2 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 550)

		data = [[
			Paragraph('<strong>INGRESOS</strong>', style_cell),
			Paragraph('<strong>DESCUENTOS</strong>', style_cell),
			Paragraph('<strong>APORTES EMPLEADOR</strong>', style_cell)
		]]
		t = Table(data, [8 * cm, 7 * cm, 5 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 575)

		h_ing = h_des = h_apor = hReal - 585
		total_ing = total_des = total_apor = 0
		for ingreso in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 43

			self.env.cr.execute(self._get_sql_wd(ingreso.code))
			res_wds = self.env.cr.dictfetchall()
			# print("res_wds",res_wds)
			if len(res_wds)>0:
				if ingreso.code == res_wds[0]['code']:
					objeto_canvas.drawRightString(first_pos, h_ing,'{:,.2f}'.format(res_wds[0]['wd_total_dias']) if res_wds[0]['wd_total_dias']>0 else '{:,.2f}'.format(res_wds[0]['wd_total_horas']))
			first_pos += size_widths[0]
			objeto_canvas.drawString(first_pos, h_ing, particionar_text(ingreso.name if ingreso.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 80, h_ing,'{:,.2f}'.format(ingreso.total) if ingreso.total else '0.00')
			first_pos += size_widths[2]

			total_ing += ingreso.total
			pagina, h_ing = verify_linea(self, objeto_canvas, wReal, hReal, h_ing, 12, pagina, size_widths)

		for descuento in CONTRIBUTIONS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 248
			objeto_canvas.drawString(first_pos, h_des, particionar_text(descuento.name if descuento.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 80, h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[2]

			total_des += descuento.total
			pagina, h_des = verify_linea(self, objeto_canvas, wReal, hReal, h_des, 12, pagina, size_widths)

		for descuento in DISCOUNTS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 248
			objeto_canvas.drawString(first_pos, h_des, particionar_text(descuento.name if descuento.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 80, h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[2]

			total_des += descuento.total
			pagina, h_des = verify_linea(self, objeto_canvas, wReal, hReal, h_des, 12, pagina, size_widths)

		for aporte in CONTRIBUTIONS_EMP:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 447
			objeto_canvas.drawString(first_pos, h_apor, particionar_text(aporte.name if aporte.name else '', 110))
			first_pos += size_widths[1]
			objeto_canvas.drawRightString(first_pos + 25, h_apor,'{:,.2f}'.format(aporte.total) if aporte.total else '0.00')
			first_pos += size_widths[2]

			total_apor += aporte.total
			pagina, h_apor = verify_linea(self, objeto_canvas, wReal, hReal, h_apor, 12, pagina, size_widths)

		data = [[
			Paragraph('TOTAL INGRESOS S/', style_title),
			Paragraph('<strong>{:,.2f}</strong>'.format(total_ing) or '0.00', style_right),
			Paragraph('TOTAL DESCUENTOS S/', style_title),
			Paragraph('<strong>{:,.2f}</strong>'.format(total_des) or '0.00', style_right),
			Paragraph('TOTAL APORTES S/', style_title),
			Paragraph('<strong>{:,.2f}</strong>'.format(total_apor) or '0.00', style_right)
		]]
		t = Table(data, [6 * cm, 2 * cm, 5 * cm, 2 * cm, 3 * cm, 2 * cm, ], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (1, -1), 0.25, colors.black),
			('BOX', (2, 0), (3, -1), 0.25, colors.black),
			('BOX', (4, 0), (5, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 705)

		data = [['',
				 Paragraph('<strong>NETO A PAGAR S/</strong>', style_cell),
				 Paragraph('<strong>{:,.2f}</strong>'.format(NET_TO_PAY.total) or '0.00', style_cell), ''
				 ]]
		t = Table(data, [7 * cm, 4 * cm, 3 * cm, 6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (1, 0), (2, -1), 0.25, colors.black),
			('BOX', (1, 0), (2, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 730)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		data = [
			[I if I else '', ''],
			[Paragraph('<strong>__________________________</strong>', style_title),
			 Paragraph('<strong>__________________________</strong>', style_title)],
			[Paragraph('<strong>EMPLEADOR</strong>', style_title),
			 Paragraph('<strong>RECIBI CONFORME <br/> TRABAJADOR</strong>', style_title)]
		]
		t = Table(data, [10 * cm, 10 * cm], 3 * [0.5 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 790)

		objeto_canvas.showPage()

		return objeto_canvas
