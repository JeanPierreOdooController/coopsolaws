# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleAnalysisBook(models.Model):
    _name = 'sale.analysis.book'
    _auto = False
    vendedor = fields.Char(string='Vendedor')
    td_partner = fields.Char(string='Tipo Doc. Partner')
    doc_partner = fields.Char(string='Doc. Partner')
    partner = fields.Char(string='Partner')
    fecha = fields.Date(string='Fecha')
    td_sunat = fields.Char(string='Tipo Doc. Factura')
    nro_comprobante = fields.Char(string='Nro Comprobante')
    estado_doc = fields.Char(string='Estado')
    category_name = fields.Char(string='Categoria')
    default_code = fields.Char(string='Referencia Interna')
    brand = fields.Char(string='Marca')
    product_id = fields.Many2one('product.product', string='Producto')
    standard_price = fields.Float(string='Costo Unitario')
    id_product = fields.Integer(string='ID Producto')
    quantity = fields.Float(string='Cantidad', digits=(12, 2))
    list_price = fields.Float(string='Precio de Lista', digits=(12, 2))
    price_unit = fields.Float(string='P. Unitario', digits=(12, 4))
    tc = fields.Float(string='TC', digits=(12, 4))
    price_total = fields.Float(string='Costo Total', digits=(64, 2), compute='_update_price_total')
    balance = fields.Float(string='Subtotal', digits=(64, 2))
    monto_dolares = fields.Float(string='Monto Dolares', digits=(64, 2))
    cuenta = fields.Char(string='Cuenta')
    moneda = fields.Char(string='Moneda')
    ref_doc = fields.Char(string='Ref Documento')
    nomenclatura = fields.Char(string='Nomenclatura')
    move_id = fields.Many2one('account.move')
    team_vendor = fields.Char(string='Equipo Vendedor', compute='_change_team')
    flag = fields.Boolean('flag')

    def _update_price_total(self):
        for i in self:
            if i.quantity and i.standard_price:
                i.price_total = i.quantity * i.standard_price
            else:
                i.price_total = 0

    @api.depends('team_vendor')
    def _change_team(self):
        for l in self:
            order = self.env['sale.order'].search(
                [('company_id', '=', l.move_id.company_id.id), ('name', '=', l.move_id.invoice_origin)])
            if order:
                if order.team_id:
                    '''
                    self.env.cr.execute("UPDATE sale_analysis_book SET team_vendor = '{}'  WHERE  id = {}".format(
                        str(order.team_id.name), l.id))
                    '''
                    l.team_vendor = order.team_id.name
                else:
                    l.team_vendor = ''
            else:
                l.team_vendor = ''
