from odoo import fields, models , api

class MOVEITTX(models.Model):
    _inherit = 'account.move'
    sale_it = fields.Many2one('sale.order', string='Orden de Venta')
    sale_it2 = fields.Many2one('sale.order', string='Orden de Venta.')
    @api.onchange('sale_it')
    def change_pur(self):
        if self.sale_it:
            self.invoice_origin = self.sale_it.name
            self.source_id = self.sale_it.source_id.id
            self.type = 'out_invoice'
            query="UPDATE account_move SET type = 'out_invoice' WHERE id = "+str(self._origin.id)
            self.env.cr.execute(query)

    @api.onchange('sale_it2')
    def change_pur2(self):
        if self.sale_it2:
            self.sale_it = self.sale_it2.id
            self.invoice_origin = self.sale_it2.name


class MOveLineIT(models.Model):
    _inherit = 'account.move.line'
    sale_line_id_it = fields.Many2one('sale.order.line',string="Vincular Linea Venta")
    sale_it = fields.Many2one('sale.order',related='move_id.sale_it')
    @api.onchange('sale_line_id_it')
    def change_pur(self):
        if self.sale_line_id_it:
            self.sale_line_ids = [(6, 0, [self.sale_line_id_it.id])]
            if self.sale_line_id_it.analytic_tag_ids:
                self.analytic_tag_ids = [(6, 0, [self.sale_line_id_it.analytic_tag_ids.ids])]
            if self.sale_line_id_it.order_id.analytic_account_id:
                self.analytic_account_id = self.sale_line_id_it.order_id.analytic_account_id.id or False