# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

##SE VUELVE A PONER EL CAMPO AQUI YA QUE SE NECESITA PARA CALCULO DE GV Y NO ES POSIBLE DEPENDER DEL CAMPO KARDEX_VALORADO_IT YA QUE ESTE DEPENDE DE GV
class stock_move(models.Model):
	_inherit = 'stock.move'

	price_unit_it = fields.Float('Precio Unitario',digits=(12,8))

class LandedCostIt(models.Model):
	_name = 'landed.cost.it'
	_description = 'Landed Cost It'
	_inherit = ['mail.thread']

	name = fields.Char(string='Nombre')

	prorratear_en = fields.Selection([('cantidad', 'Por Cantidad'), ('valor', 'Por Valor')],string='Prorratear en funcion', required=True, default='cantidad')

	picking_ids = fields.Many2many('stock.picking', 'gastos_vinculado_picking_rel', 'gastos_id', 'picking_id', string='Albaranes')
	detalle_ids = fields.One2many('landed.cost.it.line', 'gastos_id', 'Detalle')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	invoice_ids = fields.One2many('landed.cost.invoice.line', 'landed_id',string='Facturas')
	purchase_ids = fields.One2many('landed.cost.purchase.line', 'landed_id',string='Ordenes de Compra')

	state = fields.Selection([('draft', 'Borrador'), ('done', 'Finalizado')],string='Estado', default='draft')
	total_flete = fields.Float(string='Total Flete', digits=(12, 2), store=True)
	total_factor = fields.Float(string='Total Factor', digits=(12, 2), store=True)
	date_kardex = fields.Datetime(string='Fecha Kardex')
	
	def get_invoices(self):
		wizard = self.env['get.landed.invoices.wizard'].create({
			'landed_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_get_landed_invoices_wizard' % module)
		return {
			'name':u'Seleccionar Facturas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'get.landed.invoices.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def get_purchases(self):
		wizard = self.env['get.landed.purchases.wizard'].create({
			'landed_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_get_landed_purchases_wizard' % module)
		return {
			'name':u'Seleccionar Compras',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'get.landed.purchases.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	@api.onchange('invoice_ids','purchase_ids')
	def _change_flete(self):
		flete = 0
		for elem in self.purchase_ids:
			flete += elem.price_total_signed
		for elem in self.invoice_ids:
			flete += elem.debit
		self.total_flete = flete


	@api.model
	def create(self, vals):
		id_seq = self.env['ir.sequence'].search([('name', '=', 'Gastos Vinculados IT')],limit=1)

		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name': 'Gastos Vinculados IT', 'implementation': 'no_gap','active': True, 'prefix': 'GV-', 'padding': 4, 'number_increment': 1, 'number_next_actual': 1})

		vals['name'] = id_seq._next()
		t = super(LandedCostIt, self).create(vals)
		return t

	def unlink(self):
		if self.state == 'done':
			raise UserError('No se puede eliminar un Gasto Vinculado Terminado')

		for i in self.picking_ids:
			i.unlink()

		for i in self.detalle_ids:
			i.unlink()

		t = super(LandedCostIt, self).unlink()
		return t

	def borrador(self):
		self.state = 'draft'
		for i in self.detalle_ids:		
			valorizacion = self.env['stock.valuation.layer'].search([('product_id','=',i.stock_move_id.product_id.id)])
			total = 0
			for l in valorizacion:
				total += l.quantity
			if total != 0:			
				if i.valuation_id.id:
					i.valuation_id.sudo().unlink()

				new_price = (total * i.stock_move_id.product_id.standard_price ) - i.flete
				new_price = new_price / total
				i.stock_move_id.product_id.standard_price = new_price
				#nuevo_cambio = self.env['stock.change.standard.price'].create({'new_price':new_price})
				#nuevo_cambio.with_context({'active_model':'product.product','active_id':i.stock_move_id.product_id.id}).change_price()

	def procesar(self):
		self.state = 'done'
		for i in self.detalle_ids:
			valorizacion = self.env['stock.valuation.layer'].search([('product_id','=',i.stock_move_id.product_id.id)])
			total = 0
			for l in valorizacion:
				total += l.quantity
			if total != 0:			
				valuation_layer = self.env['stock.valuation.layer'].create({
                        'value': i.flete,
                        'unit_cost': 0,
                        'quantity': 0,
                        'remaining_qty': 0,
                        'description': self.name,
                        'product_id': i.stock_move_id.product_id.id,
                        'company_id': self.company_id.id,
                    })
				i.valuation_id = valuation_layer.id
				
				new_price = (total * i.stock_move_id.product_id.standard_price ) + i.flete
				new_price = new_price / total
				i.stock_move_id.product_id.standard_price = new_price
				#nuevo_cambio = self.env['stock.change.standard.price'].create({'new_price':new_price})
				#nuevo_cambio.with_context({'active_model':'product.product','active_id':i.stock_move_id.product_id.id}).change_price()
			

	def calcular(self):
		self.refresh()
		self._change_flete()
		total_fle_lines = 0
		for i in self.detalle_ids:
			i.refresh()
			total_prorrateo = 0
			for m in self.detalle_ids:
				total_prorrateo += m.cantidad_rel if self.prorratear_en == 'cantidad' else m.valor_rel

			i.factor = ((i.cantidad_rel if self.prorratear_en == 'cantidad' else i.valor_rel) /
						total_prorrateo) if total_prorrateo != 0 else 0
			i.refresh()
			i.flete = i.factor * self.total_flete
			total_fle_lines +=  i.flete

		#REDONDEO
		if len(self.detalle_ids)>0:
			diferencia_flete = 0
			if total_fle_lines < self.total_flete:
				diferencia_flete = self.total_flete - total_fle_lines
				self.detalle_ids[0].flete = self.detalle_ids[0].flete + diferencia_flete

			if total_fle_lines > self.total_flete:
				diferencia_flete = total_fle_lines - self.total_flete
				self.detalle_ids[0].flete = self.detalle_ids[0].flete - diferencia_flete

		return True

	def agregar_lineas(self):
		self.ensure_one()
		for i in self.detalle_ids:
			i.unlink()

		for i in self.picking_ids:
			for j in i.move_lines: 
				data = {
					'stock_move_id': j.id,
					'gastos_id': self.id,
				}
				self.env['landed.cost.it.line'].create(data)

class LandedCostItLine(models.Model):
	_name = 'landed.cost.it.line'
	_description = 'Landed Cost It Line'

	stock_move_id = fields.Many2one('stock.move', 'Stock Move')
	gastos_id = fields.Many2one('landed.cost.it', 'Gastos Vinculado',ondelete="cascade")

	picking_rel = fields.Many2one('stock.picking',string='Referencia', related='stock_move_id.picking_id')
	origen_rel = fields.Many2one('stock.location', string='De',related='stock_move_id.location_id')
	destino_rel = fields.Many2one('stock.location',string='Para', related='stock_move_id.location_dest_id')
	producto_rel = fields.Many2one('product.product',string='Producto', related='stock_move_id.product_id')
	unidad_rel = fields.Many2one('uom.uom',string='Unidad de Medida', related='stock_move_id.product_uom')
	cantidad_rel = fields.Float(string='Cantidad', related='stock_move_id.product_qty')
	precio_unitario_rel = fields.Float(string='Precio Unitario', related='stock_move_id.price_unit_it')
	valor_rel = fields.Float(string='Valor', compute="get_valor_rel",store=True)


	valuation_id = fields.Many2one('stock.valuation.layer','Valoracion')

	factor = fields.Float('Factor', digits=(12, 10))
	flete = fields.Float('Flete', digits=(12, 6))

	@api.depends('stock_move_id.product_qty','stock_move_id.price_unit_it')
	def get_valor_rel(self):
		for record in self:
			record.valor_rel = record.stock_move_id.product_qty * record.stock_move_id.price_unit_it

class LandedCostInvoiceLine(models.Model):
	_name = 'landed.cost.invoice.line'
	_description = 'Landed Cost Invoice Line'
	
	landed_id = fields.Many2one('landed.cost.it', 'Gastos Vinculado',ondelete="cascade")
	invoice_id = fields.Many2one('account.move.line',string='Factura')
	invoice_date = fields.Date(string='Fecha Factura')
	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	nro_comp = fields.Char(string='Nro Comprobante')
	date = fields.Date(string='Fecha Contable')
	partner_id = fields.Many2one('res.partner',string='Socio')
	product_id = fields.Many2one('product.product',string='Producto')
	debit = fields.Float(string='Debe',digits=(64,2))
	amount_currency = fields.Float(string='Monto Me',digits=(64,2))
	tc = fields.Float(string='TC',digits=(12,4))
	company_id = fields.Many2one('res.company',string=u'Compañía')

class LandedCostPurchaseLine(models.Model):
	_name = 'landed.cost.purchase.line'
	_description = 'Landed Cost Purchase Line'
	
	landed_id = fields.Many2one('landed.cost.it', 'Gastos Vinculado',ondelete="cascade")
	purchase_id = fields.Many2one('purchase.order.line',string='Compra')
	purchase_date = fields.Date(string='Fecha Pedido')
	name = fields.Char(string='Pedido')
	partner_id = fields.Many2one('res.partner',string='Socio')
	product_id = fields.Many2one('product.product',string='Producto')
	price_total_signed = fields.Float(string='Total Soles',digits=(64,2))
	tc = fields.Float(string='TC',digits=(12,4))
	currency_id = fields.Many2one('res.currency',string='Moneda')
	price_total = fields.Float(string='Total',digits=(64,2))
	company_id = fields.Many2one('res.company',string=u'Compañía')