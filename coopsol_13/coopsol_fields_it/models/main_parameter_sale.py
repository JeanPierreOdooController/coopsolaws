# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MainParameterSale(models.Model):
	_name = 'main.parameter.sale'

	name = fields.Char(default='Parametros Principales')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	quotation_manager = fields.Char(string='Encargado de Cotizaciones')
	function_manager = fields.Char(string='Cargo del Encargado')

	width_product = fields.Float(string='Anchura',digits=(12,2), default=250.00)
	height_product = fields.Float(string='Altura',digits=(12,2), default=260.00)

	color_service = fields.Char(string="Color Servicio")
	color_head = fields.Char(string="Color Cabecera")
	color_section = fields.Char(string="Color Seccion")
	color_subtotal = fields.Char(string="Color Sub Total")

	width = fields.Float(string='Anchura',digits=(12,2), default=180.00)
	height = fields.Float(string='Altura',digits=(12,2), default=60.00)

	presentation = fields.Binary(string="Representante")

	@api.constrains('company_id')
	def _check_unique_parameter(self):
		self.env.cr.execute("""select id from main_parameter_sale where company_id = %s""" % (str(self.company_id.id)))
		res = self.env.cr.dictfetchall()
		if len(res) > 1:
			raise UserError(u"Ya existen Parametros Principales para esta Compañía")

	def _check_parameters(self):
		for i in self:
			if not i.color_service or not i.color_head or not i.color_section or not i.color_subtotal or not i.presentation or not i.width or not i.height:
				raise UserError(u'Termine de configurar los Parámetros para su reporte.')