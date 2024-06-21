# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    reservado = fields.Float('Reservado')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['reservado'] = ",(select sum(sml.product_uom_qty) from stock_move_line sml  inner join stock_move sm on sm.id = sml.move_id inner join sale_order_line sol on sol.id = sm.sale_line_id where sol.order_id = s.id and l.product_id = sml.product_id and sml.state in ('partially_available','assigned'))  as reservado"
        
        #groupby += ', l.id'
        #from_clause += '  left join product_brand pb on pb.id = t.product_brand_id'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
