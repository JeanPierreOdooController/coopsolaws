from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockProductionLotChange(models.Model):
    _inherit = 'stock.production.lot'

    cant_store = fields.Float(string='', digits=(10, 2), related='product_qty', store=True)


class StockPickingChangeTest(models.Model):
    _inherit = 'stock.picking'

    tipo_operacion_temp = fields.Selection([
        ('incoming', 'Recibo'),
        ('outgoing', 'Entrega'),
        ('internal', 'Transferencia interna'),
    ], string='OP', related='picking_type_id.code', store=True)


class StockMoveChangeTest(models.Model):
    _inherit = 'stock.move'

    tipo_operacion_temp = fields.Selection([
        ('incoming', 'Recibo'),
        ('outgoing', 'Entrega'),
        ('internal', 'Transferencia interna'),
    ], string='OP', related='picking_id.picking_type_id.code', store=True)


class StockMoveLineChangeTest(models.Model):
    _inherit = 'stock.move.line'

    lot_ids_domain = fields.Many2many('stock.production.lot', string='Lotes dominio',
                                      compute='_compute_product_id_domain')

    def _compute_product_id_domain(self):
        for rec in self:
            # jala de "DE ALMACEN"
            rec.lot_ids_domain = []

            if rec.product_id.tracking == 'lot' and rec.picking_id.picking_type_id not in ['cancel', 'done']:
                ids_lotes_quant = []
                if rec.picking_id.picking_type_id.code == 'outgoing' or rec.picking_id.picking_type_id.code == 'internal':
                    ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                         ('quantity', '>', 0), ('location_id', '=', rec.location_id.id)])
                else:  # compras incoming
                    ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                         ('location_id', '=', rec.location_dest_id.id)])

                rec.lot_ids_domain = ids_lotes_quant.lot_id.ids

                # to get cantidad lote
                if rec.lot_id and ids_lotes_quant:
                    lotes_cantidad = []
                    for lote in ids_lotes_quant:
                        if lote.lot_id == rec.lot_id:
                            lotes_cantidad.append(lote)

                    if lotes_cantidad:
                        rec.lot_id_qty = 0
                        for lote in lotes_cantidad:
                            rec.lot_id_qty += lote.quantity

            else:
                rec.lot_id_qty += rec.product_id.qty_available

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id.tracking == 'lot':
                ids_lotes_quant = []
                if rec.picking_id.picking_type_id.code == 'outgoing' or rec.picking_id.picking_type_id.code == 'internal':
                    ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                         ('quantity', '>', 0), ('location_id', '=', rec.location_id.id)])
                else:  # compras incoming
                    ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                         ('location_id', '=', rec.location_dest_id.id)])
                return {
                    'domain': {
                        'lot_id': [('id', 'in', ids_lotes_quant.lot_id.ids)]
                    }
                }

            else:
                rec.lot_id_qty += rec.product_id.qty_available
