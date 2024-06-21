from odoo import models, fields, api
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
import base64
from dateutil.relativedelta import relativedelta

class stock_picking_type(models.Model):
	_inherit='stock.picking.type'

	validate_locations = fields.Boolean('Verificar ubicaciones')

class StockPicking(models.Model):
	_inherit = 'stock.picking'



	@api.model
	def create(self,vals):
		type_picking = self.env['stock.picking.type'].browse(vals['picking_type_id'])
		if type_picking.validate_locations==True:
			if vals['location_id']==vals['location_dest_id']:
				raise UserError(u'La Ubicación de origen no puede ser la misma que la ubicación de destino')
		return super(StockPicking,self).create(vals)

	def write(self,vals):
		type_picking=self.picking_type_id
		if 'picking_type_id' in vals:
			type_picking = self.env['stock.picking.type'].browse(vals['picking_type_id'])

		if type_picking.validate_locations==True:
			if 'location_id' in vals and 'location_dest_id' in vals:
				if vals['location_id']==vals['location_dest_id']:
					raise UserError(u'La Ubicación de origen no puede ser la misma que la ubicación de destino')
			if 'location_id' in vals and 'location_dest_id' not in vals:
				if vals['location_id']==self.location_dest_id.id:
					raise UserError(u'La Ubicación de origen no puede ser la misma que la ubicación de destino')
			if 'location_id' not in vals and 'location_dest_id' in vals:
				if vals['location_dest_id']==self.location_id.id:
					raise UserError(u'La Ubicación de origen no puede ser la misma que la ubicación de destino')
			if self.location_dest_id==self.location_id.id:
				raise UserError(u'La Ubicación de origen no puede ser la misma que la ubicación de destino')
		return super(StockPicking,self).write(vals)

