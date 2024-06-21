# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResCompany(models.Model):
	_inherit = 'res.company'

	slogan = fields.Char(string='Lema')
	reference = fields.Char(string='Referencia')
	color_service = fields.Char(string="Color Servicio",compute="get_colors")
	color_head = fields.Char(string="Color Cabecera",compute="get_colors")
	color_section = fields.Char(string="Color Seccion",compute="get_colors")
	color_subtotal = fields.Char(string="Color Sub Total",compute="get_colors")
	presentation = fields.Binary(string="Representante",compute="get_colors")
	def get_colors(self):
		for record in self:
			record.color_service = False
			record.color_head = False
			record.color_section = False
			record.color_subtotal = False
			record.presentation = False
			company = self.env['main.parameter.sale'].search([('company_id','=',record.id)],limit=1)
			if company:
				record.color_service = company.color_service
				record.color_head = company.color_head
				record.color_section = company.color_section
				record.color_subtotal = company.color_subtotal
				record.presentation = company.presentation