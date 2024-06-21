from openerp.osv import osv
import base64
from openerp import models, fields, api, exceptions, _

from odoo.exceptions import UserError


class LineMoveGuideLine(models.Model):
    _inherit = 'move.guide.line'
    picking_id = fields.Many2one('stock.picking', string="ALBARAN", compute="get_albaran")

    @api.depends('numberg')
    def get_albaran(self):
        for record in self:
            p = self.env['stock.picking'].search([('numberg', '=', record.numberg),('state','=','done')], limit=1)
            record.picking_id = p.id if p else None

'''

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        Sale = self.env['sale.order'].browse(self._context.get('active_id', False))
        before_invoices = Sale.invoice_ids
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        after_invoices = Sale.invoice_ids
        new_invoice = after_invoices - before_invoices
        if len(new_invoice) == 1:
            self.picking_ids.write({'invoice_id': new_invoice.id})
            ebill = self.env['ir.module.module'].search([('name', '=', 'ebill')])
            if ebill and ebill.state == 'installed':
                for picking in self.picking_ids:
                    self.env['move.guide.line'].create({
                        'move_id': new_invoice.id,
                        'numberg': picking.numberg
                    })
                new_invoice.action_set_descripcion()
        return res
        
'''


class FcaturaIT(models.Model):
    _inherit = 'account.move'
    picking_id_it = fields.Many2one('stock.picking', string="ALBARAN")
    first_update_descripcion = fields.Boolean(string="PRIMERA ACTUALIZACION DE DESCRICPION",default=False)

    @api.onchange('guide_line_ids')
    def action_set_descripcion(self):

        for record in self:
            if record.guide_line_ids and not record.first_update_descripcion:

                idsg = []
                for r in record.guide_line_ids:
                    if r.picking_id:
                        idsg.append(r.picking_id.id)
                # raise ValueError(idsg)
                for l in record.invoice_line_ids:
                    pi = self.env['stock.move'].search([('picking_id', 'in', idsg),
                                                        ('product_id', '=', l.product_id._origin.id)])
                    #raise ValueError(pi)
                    ids = []
                    for p in pi:
                        ids.append(p.id)
                    l.picking_lines_id_it = [(6, 0, ids)]
                    l.change_descripcion_it()
                record.first_update_descripcion = True

    albaran_ids_filter = fields.Many2many('stock.picking', compute="search_albaranes_pedido")



    def _compute_amount(self):
        res = super(FcaturaIT, self)._compute_amount()
        self.action_set_descripcion()

        return res
    


    def search_albaranes_pedido(self):
        for record in self:
            sale_ids = []
            for l in record.invoice_line_ids:
                for s in l.sale_line_ids:
                    if not s.order_id in sale_ids:
                        sale_ids.append(s.order_id)
            albaran_ids = []
            for sx in sale_ids:
                for p in sx.picking_ids:
                    if not p.id in albaran_ids:
                        albaran_ids.append(p.id)
            record.albaran_ids_filter = [(6, 0, albaran_ids)]


class MOveLineIT(models.Model):
    _inherit = 'account.move.line'
    picking_line_id_it = fields.Many2one('stock.move')
    picking_id_it = fields.Many2one(related="move_id.picking_id_it")
    picking_lines_id_it = fields.Many2many('stock.move')



    @api.onchange('picking_lines_id_it')
    def change_descripcion_it(self):
        for record in self:

            texto = record.product_id.name
            if record.sale_line_ids:
                texto = record.sale_line_ids[0].name
            for r in record.picking_lines_id_it:
                tracking_init = r.tracking_it
                tracking = r.tracking_it
                texto2 = ''
                c = 0

                if tracking == 'serial':
                    tracking = 'Series:'

                if tracking == 'lot':
                    tracking = 'Lotes:'

                if tracking == 'none':
                    tracking = ''

                for l in r.move_line_ids:
                    if l.lot_id and tracking_init in ['lot', 'serial']:

                        if l.lot_id.name:
                            c += 1
                            fv = str(l.lot_id.life_date.strftime('%Y-%m-%d')) if l.lot_id.life_date else None
                            if fv:
                                fv = " F.V.: " + fv
                            else:
                                fv = ''


                        texto2 += "- " + str(l.lot_id.name) + "  Cant: " + str(l.qty_done) + fv + "\n"
                        c += 1
                if c > 0:
                    texto += "\n"
                    texto += tracking + "\n"
                    texto += texto2
            record.name = texto
