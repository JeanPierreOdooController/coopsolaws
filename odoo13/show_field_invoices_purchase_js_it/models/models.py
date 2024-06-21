from odoo import fields, models , api
class MoveIT(models.Model):
    _inherit = 'account.move'
    purchase_it = fields.Many2one('purchase.order',string='Orden de Compra')
    edit_lines_it = fields.Boolean(compute='get_edit_lines_it',default=True)
    search_force_po = fields.Boolean(string="Buscar (Compras / Ventas) con facturas")
    purchase_it2 = fields.Many2one('purchase.order', string='Orden de Compra.')

    def get_edit_lines_it(self):
        for record in self:
            vv = False
            p = self.env.user.has_group("show_field_invoices_purchase_js_it.group_vincular_facturas_compras")
            if p == True or record.state == 'draft':
                vv = True
            record.edit_lines_it = vv

    @api.onchange('purchase_it')
    def change_pur(self):
        if self.purchase_it:
            self.invoice_origin = self.purchase_it.name

    @api.onchange('purchase_it2')
    def change_pur2(self):
        if self.purchase_it2:
            self.purchase_it = self.purchase_it2.id
            self.invoice_origin = self.purchase_it2.name

class MOveLine(models.Model):
    _inherit = 'account.move.line'
    purchase_it = fields.Many2one('purchase.order',related='move_id.purchase_it')