# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	contact_id = fields.Many2one('res.partner',string='Contacto')
	service_type_id = fields.Many2one('service.type.coopsol',string='Tipo Servicio')

class ServiceTypeCoopsol(models.Model):
	_name = 'service.type.coopsol'

	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo')
