from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import uuid


class SaleOrderChangeAction(models.Model):
    _inherit = 'sale.order'

    def open_wizard_invoice_state(self):
        return {
            'name': 'Cambiar Estado Factura',
            'res_model': 'sale.change.invoice.state.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_order_ids': self.ids},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def open_wizard_state(self):
        return {
            'name': 'Cambiar Estado Venta',
            'res_model': 'sale.change.state.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_order_ids': self.ids},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class SaleChangeInvoiceStateWizard(models.TransientModel):
    _name = 'sale.change.invoice.state.wizard'
    _description = 'Sale Change Invoice State Wizard'

    order_ids = fields.Many2many('sale.order', string='Venta')
    invoice_status = fields.Selection([
        ('upselling', 'Oportunida de upselling'),
        ('invoiced', 'Facturado'),
        ('to invoice', 'A facturar'),
        ('no', 'Nada que facturar'),
    ], string='Estado de Factura', required=True)
    state_to_change = fields.Selection([
        ('draft', 'Cotización'),
        ('sent', 'Presupuesto Enviado'),
        ('sale', 'Órdenes de Venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', required=True, readonly=True)

    @api.onchange('invoice_status')
    def _onchange_invoice_status(self):
        if self.invoice_status == 'invoiced' or self.invoice_status == 'to invoice':
            self.state_to_change = 'done'
        elif self.invoice_status == 'no':
            self.state_to_change = 'cancel'

    def change_invoice_state(self):
        if self.invoice_status == 'invoiced' or self.invoice_status == 'to invoice':
            self.state_to_change = 'done'
        elif self.invoice_status == 'no':
            self.state_to_change = 'cancel'

        for sale in self.order_ids:
            # print()
            # print()
            # print()
            # print()
            # print(self.invoice_status)
            # print(sale.invoice_status)
            # print()
            if sale.state == 'done':
                sale.state == 'cancel'
            sale.state = self.state_to_change
            sale.invoice_status = self.invoice_status
            # print(self.invoice_status)
            # print(sale.invoice_status)
            # input()


class SaleChangeStateWizard(models.TransientModel):
    _name = 'sale.change.state.wizard'
    _description = 'Sale Change State Wizard'

    order_ids = fields.Many2many('sale.order', string='Venta')
    state = fields.Selection([
        ('draft', 'Cotización'),
        ('sent', 'Presupuesto Enviado'),
        ('sale', 'Órdenes de Venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', required=True)

    def change_state(self):
        for sale in self.order_ids:
            sale.state = self.state
