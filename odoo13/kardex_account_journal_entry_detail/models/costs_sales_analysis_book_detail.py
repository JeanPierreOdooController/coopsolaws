# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CostsSalesAnalysisBookDetail(models.Model):
	_name = 'costs.sales.analysis.book.detail'
	
	almacen = fields.Char(string=u'Almacén')
	origen = fields.Char(string=u'Origen')
	destino = fields.Char(string=u'Destino')
	doc = fields.Char(string=u'Documento')
	date = fields.Date(string=u'Fecha')
	producto = fields.Char(string=u'Producto')
	cantidad = fields.Float(string='Cantidad', digits=(64,2))
	valor = fields.Float(string='Valor', digits=(64,2))
	valuation_account_id = fields.Many2one('account.account',string=u'Cuenta Producto')
	input_account_id = fields.Many2one('account.account',string=u'Cuenta Variación')
	output_account_id = fields.Many2one('account.account',string=u'Cuenta Costo de Venta')
	user_id = fields.Many2one('res.users',string='Usuario')