from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


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

    def button_validate(self):
        for rec in self:
            # check cantidad solicitada
            products = {}
            for move in rec.move_ids_without_package:
                if move.product_id in products.keys():
                    products[move.product_id][0] += move.product_uom_qty
                else:
                    products[move.product_id] = [move.product_uom_qty, 0]
                # products[move.product_id] = [move.quantity_done, 0]

            # add all operaciones detalladas
            for move_line in rec.move_line_ids_without_package:
                if move_line.product_id in products.keys():
                    products[move_line.product_id][1] += move_line.qty_done

            # comparacion
            for product_key in products.keys():
                if products[product_key][0] < products[product_key][1]:
                    raise UserError('La cantidad "Realizada" para el Producto %s sobrepasa la Cantidad requerida'%(product_key.display_name) + ' [' + str(products[product_key][0]) + ' and ' + str(products[product_key][1]) + ']')
        return super(StockPickingChangeTest, self).button_validate()


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
    cant_lote_unico = fields.Float(string='Stock Lote/Serie', compute='_compute_product_id_domain')
    cant_lote_total = fields.Float(string='Stock Total', digits=(10,2), compute='_compute_product_id_domain')
    trazabilidad = fields.Char(string='Trazabilidad')


    def _compute_product_id_domain(self):
        for rec in self:
            # jala de "DE ALMACEN"
            rec.lot_ids_domain = []
            rec.cant_lote_unico = 0
            rec.cant_lote_total = 0
            por_devolucion = False
            por_recepcion = False

            if rec.product_id and rec.picking_id.state not in ['cancel']:
                ids_lotes_quant = []
                # get lote
                if rec.picking_id.picking_type_id.code in ['outgoing', 'internal']:
                    if rec.picking_id.picking_type_id.code == 'internal' and rec.picking_id.picking_type_id.name == 'Transferencias internas':
                        ids_lotes_quant = rec.env['stock.quant'].search(
                            [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                            ('quantity', '>', 0), ('location_id', '=', rec.location_dest_id.id)])
                    else:
                        ids_lotes_quant = rec.env['stock.quant'].search(
                            [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                            ('quantity', '>', 0), ('location_id', '=', rec.location_id.id)])
                else:  # compras incoming
                    if rec.picking_id.origin and rec.picking_id.origin.find('Retorno de ') >= 0:
                        albaran_para_devolver = rec.picking_id.origin[len('Retorno de '):]
                        albaran_para_devolver = rec.env['stock.picking'].search(
                                [('name', '=', albaran_para_devolver), ('company_id', '=', rec.company_id.id)])
                        if len(albaran_para_devolver) == 0:
                            raise ValidationError('No puede encontrar Albarán del cual Devolver')
                        if len(albaran_para_devolver) > 1:
                            raise ValidationError('Más de 1 Albarán para devolver, solo deberia haber 1')

                        ids_lotes_quant = []
                        for line in albaran_para_devolver.move_line_ids_without_package:
                            if line.product_id == rec.product_id and line.lot_id:
                                ids_lotes_quant.append(line.lot_id.id)
                        ids_lotes_quant = self.env['stock.production.lot'].search( [('id', 'in', ids_lotes_quant)] )
                        por_devolucion = True
                    elif rec.picking_id.origin:
                        ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                        ('location_id', '=', rec.location_dest_id.id)])
                    else:
                        # ids_lotes_quant = rec.env['stock.quant'].search(
                        # [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
                        ids_lotes_quant = rec.env['stock.production.lot'].search([('company_id', '=', rec.company_id.id), ('product_id', '=', rec.product_id.id)])
                        por_recepcion = True

                # FOR DOMAIN
                if por_recepcion:
                    rec.lot_ids_domain = ids_lotes_quant.ids
                elif not por_devolucion:
                    rec.lot_ids_domain = ids_lotes_quant.lot_id.ids
                else:
                    rec.lot_ids_domain = ids_lotes_quant.ids

                # to get cantidad total and unico lote
                if not por_recepcion:
                    if rec.product_id.tracking in ['lot', 'serial']:
                        if ids_lotes_quant:
                            if not por_devolucion:
                                rec_cant_lote_total = 0
                                rec_cant_lote_unico = 0
                                for lote in ids_lotes_quant:
                                    rec_cant_lote_total += lote.quantity
                                    if lote.lot_id == rec.lot_id:
                                        rec_cant_lote_unico += lote.quantity
                                rec.cant_lote_total = rec_cant_lote_total
                                rec.cant_lote_unico = 0
                                if rec.lot_id:
                                    rec.cant_lote_unico = rec_cant_lote_unico
                    else:
                        if ids_lotes_quant:
                            if not por_devolucion:
                                rec.cant_lote_total = 0
                                for lote in ids_lotes_quant:
                                    rec.cant_lote_total += lote.quantity
                                rec.cant_lote_unico = rec.cant_lote_total

            # TRAZABILIDAD
            rec.trazabilidad = ''
            if rec.product_id:
                rec.trazabilidad = rec.product_id.tracking

    # aqui se hace la validación en el compute no ya que el onchange 
    # es al instante el cpumte validaria todos siempre
    @api.onchange('product_id', 'lot_id')
    def _onchange_product_id(self):
        for rec in self:
            # jala de "DE ALMACEN"
            rec.lot_ids_domain = []
            por_devolucion = False
            por_recepcion = False

            if rec.product_id:
                # TRAZABILIDAD
                rec.trazabilidad = rec.product_id.tracking

                ids_lotes_quant = []
                # get lote
                if rec.picking_id.picking_type_id.code in ['outgoing', 'internal']:
                    if rec.picking_id.picking_type_id.code == 'internal' and rec.picking_id.picking_type_id.name == 'Transferencias internas':
                        ids_lotes_quant = rec.env['stock.quant'].search(
                            [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                            ('quantity', '>', 0), ('location_id', '=', rec.location_dest_id.id)])
                    else:
                        ids_lotes_quant = rec.env['stock.quant'].search(
                            [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                            ('quantity', '>', 0), ('location_id', '=', rec.location_id.id)])
                else:  # compras incoming
                    if rec.picking_id.origin and rec.picking_id.origin.find('Retorno de ') >= 0:
                        albaran_para_devolver = rec.picking_id.origin[len('Retorno de '):]
                        albaran_para_devolver = rec.env['stock.picking'].search(
                                [('name', '=', albaran_para_devolver), ('company_id', '=', rec.company_id.id)])
                        if len(albaran_para_devolver) == 0:
                            raise ValidationError('No puede encontrar Albarán del cual Devolver')
                        if len(albaran_para_devolver) > 1:
                            raise ValidationError('Más de 1 Albarán para devolver, solo deberia haber 1')

                        ids_lotes_quant = []
                        for line in albaran_para_devolver.move_line_ids_without_package:
                            if line.product_id == rec.product_id and line.lot_id:
                                ids_lotes_quant.append(line.lot_id.id)
                        ids_lotes_quant = self.env['stock.production.lot'].search( [('id', 'in', ids_lotes_quant)] )
                        por_devolucion = True
                    elif rec.picking_id.origin:
                        ids_lotes_quant = rec.env['stock.quant'].search(
                        [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id),
                        ('location_id', '=', rec.location_dest_id.id)])
                    else:
                        # ids_lotes_quant = rec.env['stock.quant'].search(
                        # [('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
                        ids_lotes_quant = rec.env['stock.production.lot'].search([('company_id', '=', rec.company_id.id), ('product_id', '=', rec.product_id.id)])
                        por_recepcion = True

                # FOR DOMAIN
                if por_recepcion:
                    rec.lot_ids_domain = ids_lotes_quant.ids
                elif not por_devolucion:
                    rec.lot_ids_domain = ids_lotes_quant.lot_id.ids
                else:
                    rec.lot_ids_domain = ids_lotes_quant.ids

                # to get cantidad total and unico lote
                if not por_recepcion:
                    if rec.product_id.tracking in ['lot', 'serial']:
                        if ids_lotes_quant:
                            if not por_devolucion:
                                rec_cant_lote_total = 0
                                rec_cant_lote_unico = 0
                                for lote in ids_lotes_quant:
                                    rec_cant_lote_total += lote.quantity
                                    if lote.lot_id == rec.lot_id:
                                        rec_cant_lote_unico += lote.quantity
                                rec.cant_lote_total = rec_cant_lote_total
                                rec.cant_lote_unico = 0
                                if rec.lot_id:
                                    rec.cant_lote_unico = rec_cant_lote_unico


                        if rec.picking_id.picking_type_id.code != 'incoming':
                        # check qty_done no pueden sacar mas de lo q existe
                            if rec.qty_done and rec.cant_lote_total and rec.qty_done > rec.cant_lote_total:
                                raise ValidationError(
                                    'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')
                            if rec.qty_done and rec.cant_lote_unico and rec.qty_done > rec.cant_lote_unico:
                                raise ValidationError(
                                    'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')
                        # to domin in series and lots
                        if not por_devolucion:
                            return {
                                'domain': {
                                    'lot_id': [('id', 'in', ids_lotes_quant.lot_id.ids)]
                                }
                            }
                        else:
                            return {
                                'domain': {
                                    'lot_id': [('id', 'in', ids_lotes_quant.ids)]
                                }
                            }
                    else:
                        if ids_lotes_quant:
                            rec.cant_lote_total = 0
                            for lote in ids_lotes_quant:
                                rec.cant_lote_total += lote.quantity
                            rec.cant_lote_unico = rec.cant_lote_total

                        # check qty_done no pueden sacar mas de lo q existe
                            # check qty_done no pueden sacar mas de lo q existe
                            if rec.picking_id.picking_type_id.code != 'incoming':
                                if rec.qty_done and rec.cant_lote_total and rec.qty_done > rec.cant_lote_total:
                                    raise ValidationError(
                                        'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')
                                if rec.qty_done and rec.cant_lote_unico and rec.qty_done > rec.cant_lote_unico:
                                    raise ValidationError(
                                        'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')
            else:
                rec.cant_lote_total = 0
                rec.cant_lote_unico = 0

    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        for rec in self:
            if rec.product_id and rec.picking_id.picking_type_id.code != 'incoming':
                # check qty_done no pueden sacar mas de lo q existe
                if rec.qty_done and rec.cant_lote_total and rec.qty_done > rec.cant_lote_total:
                    raise ValidationError(
                        'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')
                if rec.qty_done and rec.cant_lote_unico and rec.qty_done > rec.cant_lote_unico:
                    raise ValidationError(
                        'El ' + rec.product_id.name + ' no puede sacar mas productos de los que existen')

    # def button_validate(self):
    #     for pick in self:
    #         if pick.picking_type_id.code == 'outgoing':
    #             for line in pick.move_line_ids_without_package:
    #                 if line.lot_id:
    #                     default_uom = line.lot_id.product_id.uom_id
    #                     qty = default_uom._compute_quantity(line.qty_done, line.product_uom_id)
    #                     if qty > line.lot_id.product_qty:
    #                         raise UserError('La cantidad "Realizada" para el Producto %s sobrepasa la Cantidad del Lote'%(line.product_id.display_name))
    #     return super(StockPicking,self).button_validate()
