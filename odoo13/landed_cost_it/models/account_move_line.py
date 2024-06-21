# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	
	#invoice_id = fields.Many2one('account.move.line',string='Factura')
	invoice_date_landed = fields.Date(related='move_id.invoice_date',string='Fecha Factura')
	is_landed = fields.Boolean(related='product_id.product_tmpl_id.is_landed_cost',string='Usa GV')
	#type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	#nro_comp = fields.Char(string='Nro Comprobante')
	#date = fields.Date(string='Fecha Contable')
	#partner_id = fields.Many2one('res.partner',string='Socio')
	#product_id = fields.Many2one('product.product',string='Producto')
	#debit = fields.Float(string='Debe',digits=(64,2))
	#amount_currency = fields.Float(string='Monto Me',digits=(64,2))
	#tc = fields.Float(string='TC',digits=(12,4))
	#company_id = fields.Many2one('res.company',string=u'Compañía')