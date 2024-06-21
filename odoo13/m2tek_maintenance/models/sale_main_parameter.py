# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class product_modelo(models.Model):
	_name ='product.modelo'

	name = fields.Char('Modelo')


class product_template(models.Model):
	_inherit ='product.template'

	modelo = fields.Many2one('product.modelo','Modelo')


class maintenance_period(models.Model):
	_name = 'maintenance.period'

	name = fields.Char('Periodo',required=True)
	meses = fields.Integer('Cantidad de Meses',required=True,default=1)


class MaintenanceComponentLine(models.Model):
	_name = 'maintenance.component.line'

	request_id = fields.Many2one('maintenance.request')
	component_id = fields.Many2one('maintenance.component', string='Componente')
	product_id = fields.Many2one('product.product', string='Producto')
	lot_id = fields.Many2one('stock.production.lot', string='Codigo')
	quantity = fields.Float('Cantidad')
	notes = fields.Char(string='Observaciones')
	name=fields.Char(u'Línea de Pedido',compute='get_line_name',store=True)

	def get_line_name(self):
		for l in self:
			l.name=(l.request_id.name if l.request_id else '')+' - '+(l.product_id.name if l.product_id else '')+': '+(str(l.quantity) if l.quantity else '0')	

class MaintenanceComponent(models.Model):
	_name = 'maintenance.component'

	name = fields.Char(string='Nombre')

	
class Paquetes(models.Model):
	_name = 'paquete.paradox'
	name_str  = fields.Char(string="Nombre",required=True)
	code = fields.Char(string="Codigo",required=True, copy=False,
						readonly=True, default=lambda self: ('New'))
	company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
								 default=lambda self: self.env.company)
	name = fields.Char(string="Nombre",compute="get_name")
	lines_ids  = fields.One2many('paquete.line','paquete_id')
	@api.model
	def create(self, vals):
		seq_date = None
		if 'company_id' in vals:
			vals['code'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
				'pqt', sequence_date=seq_date) or 'New'
		else:
			vals['code'] = self.env['ir.sequence'].next_by_code('pqt', sequence_date=seq_date) or 'New'
		result = super(Paquetes, self).create(vals)
		return result
	def get_name(self):
		for record in self:
			record.name  = str(record.code) + '/'+str(record.name_str)


class PaqueteLine(models.Model):
	_name   = 'paquete.line'
	component_id = fields.Many2one('maintenance.component',string="Componente")
	product_id  = fields.Many2one('product.product',string="Producto",required=True)
	product_qty = fields.Float(string="Cantidad")
	product_uom = fields.Many2one('uom.uom',string="Udm",required=True)
	product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
	paquete_id = fields.Many2one('paquete.paradox')
	notes = fields.Char(string="Observacion")


class maintenance_request(models.Model):
	_inherit = 'maintenance.request'

	date_teoric = fields.Date(u'Fecha Teórica',track_visibility='always')
	product_comercial = fields.Many2one('product.product','Producto o Servicio Comercial')
	pedido_venta = fields.Many2one('sale.order','Pedido de Venta')
	paquete = fields.Many2one('','Paquete de Mantenimiento')

class maintenance_equipment(models.Model):
	_inherit = 'maintenance.equipment'

	lot_id = fields.Many2one('stock.production.lot','Número de Serie')
	product_brand_id = fields.Many2one('product.brand',related='lot_id.product_id.product_brand_id')
	modelo = fields.Many2one('product.modelo',related='lot_id.product_id.modelo')
	product_id = fields.Many2one('product.product',related='lot_id.product_id')

	stock_move_id = fields.Many2one('stock.move','Linea de Albaran de Salida',compute="get_stock_move_id")
	picking_id = fields.Many2one('stock.picking','Albaran de Salida',related="stock_move_id.picking_id")
	move_id = fields.Many2one('account.move','Factura de Venta',related="stock_move_id.invoice_id")
	guia_remision = fields.Char('Guia de Remision',related="picking_id.numerg")


	def get_stock_move_id(self):
		for i in self:
			lineas = self.env['stock.move.line'].search([('product_id','=',i.product_id.id),('location_dest_id.usage','=','customer'),('picking_id.state','=','done'),('lot_id','=',i.lot_id.id)])
			if len(lineas) >0:
				i.stock_move_id = lineas[0].move_id
			else:
				i.stock_move_id = False

	garantia = fields.Many2one('maintenance.period','Garantia')
	frecuencia = fields.Many2one('maintenance.period','Frecuencia')

	def generar_mantenimientos(self):
		for i in self:
			empleado = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
			data = {
				'name': 'Mantenimiento :' + (i.lot_id.name if i.lot_id.name else '') + ' - ' + (i.product_id.name_get()[0][1] if i.product_id.id else ''),
				'employee_id': empleado.id,
				'equipment_id': i.id,
				'request_date': ,
				'maintenance_team_id': self.env['maintenance.team'].search([])[0].id if len(self.env['maintenance.team'].search([]))>0 else False,
			}