from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockMoveStockFilterLote(models.Model):
    _inherit = 'stock.move'

    cant_disponible = fields.Float(string='Cantidad Disponible', compute="_compute_cant_disponible")

    def _compute_cant_disponible(self):
        for rec in self:
            rec.cant_disponible = 0
            if rec.picking_id.state not in ['cancel']:
                if rec.product_id:
                    ids_lotes_quant = 0
                    if rec.picking_id.picking_type_id.code == 'outgoing' or rec.picking_id.picking_type_id.code == 'internal':
                        ids_lotes_quant = rec.env['stock.quant'].search(
                            [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                            ('quantity', '>', 0), ('location_id', '=', rec.picking_id.location_id.id)])
                    else:  # compras incoming
                        ids_lotes_quant = rec.env['stock.quant'].search(
                            [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                            ('location_id', '=', rec.picking_id.location_dest_id.id)])
                    if ids_lotes_quant:
                        rec.cant_disponible = 0
                        for lote in ids_lotes_quant:
                            rec.cant_disponible += lote.quantity
                else:
                    rec.cant_disponible = 0


    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                ids_lotes_quant = 0
                if rec.picking_id.picking_type_id.code == 'outgoing' or rec.picking_id.picking_type_id.code == 'internal':
                    ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                         ('quantity', '>', 0), ('location_id', '=', rec.picking_id.location_id.id)])
                else:  # compras incoming
                    ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                         ('location_id', '=', rec.picking_id.location_dest_id.id)])
                if ids_lotes_quant:
                    rec.cant_disponible = 0
                    for lote in ids_lotes_quant:
                        rec.cant_disponible += lote.quantity
                if rec.cant_disponible and rec.quantity_done and rec.cant_disponible < rec.quantity_done:
                    raise ValidationError(
                        'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')
            else:
                rec.cant_disponible = 0

    @api.onchange('quantity_done')
    def _onchange_quantity_done_cant_disponible(self):
        for rec in self:
            if rec.cant_disponible and rec.quantity_done and rec.cant_disponible < rec.quantity_done:
                raise ValidationError(
                    'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')

