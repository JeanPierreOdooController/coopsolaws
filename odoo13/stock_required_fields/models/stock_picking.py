# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class stock_picking(models.Model):
	_inherit = 'stock.picking'

	def button_validate(self):
		if self.picking_type_code == 'outgoing':
			if self.serie_guia.id==False:
				raise UserError(u'El campo "Serie Guía" no puede estar vacio')
			if self.numberg==False:
				raise UserError(u'El campo "# Guía de remision" no puede estar vacio')
			if self.carrier_id_it.id==False:
				raise UserError(u'El campo "Transportista" no puede estar vacio')
			if self.vehicle_id.id==False:
				raise UserError(u'El campo "Vehículo" no puede estar vacio')
			if self.driver_id.id==False:
				raise UserError(u'El campo "Conductor" no puede estar vacio')
			if self.type_of_transport==False:
				raise UserError(u'El campo "Tipo de Transporte" no puede estar vacio')
			if self.reason_transfer.id==False:
				raise UserError(u'El campo "Motivo de Traslado" no puede estar vacio')
		return super(stock_picking,self).button_validate()