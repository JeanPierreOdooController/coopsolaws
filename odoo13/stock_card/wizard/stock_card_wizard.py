# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models

class StockCardWizard(models.TransientModel):
    _name = 'stock.card.wizard'

    location_id = fields.Many2one('stock.location', string='Ubicacion')
    product_id = fields.Many2one('product.product', string='Producto')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date", default=fields.Date.today)

    
    def print_xls_report(self, context=None):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.card.wizard'
        datas['form'] = self.read()[0]
        return self.env.ref('stock_card.card_report_xls').report_action(self, data=datas)