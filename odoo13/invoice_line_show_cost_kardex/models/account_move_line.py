# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    cost_kardex = fields.Float(string="costo unitario S/.",compute="get_costokrdx_lin")


    def get_costokrdx_lin(self):
        for i in self:
            costo = 0
            cantidad = 0
            if i.move_id.type == "out_invoice":
                for lin in i.sale_line_ids.move_ids:
                    if lin.state=="done":
                        costo += lin.price_unit_it * lin.quantity_done
                        cantidad += lin.quantity_done
                if costo==0 and i.product_id.id and i.move_id.type=="out_invoice":
                    for sm in self.env["stock.move"].sudo().search([("invoice_id","=",i.move_id.id),("state","=","done"),("product_id","=",i.product_id.id)]):
                        costo += sm.price_unit_it * sm.quantity_done
                        cantidad += sm.quantity_done
            i.cost_kardex = (costo / cantidad) if cantidad != 0 else 0



class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    cost_kardex = fields.Float(string="costo unitario S/.",compute="get_costokrdx_lin")
    cost_kardex_dolar = fields.Float(string="costo unitario $",compute="get_costokrdx_lin")


    @api.onchange("product_id")
    def get_costokrdx_lin(self):
        for i in self:
            costo = 0
            cantidad = 0
            for lin in i.move_ids:
                if lin.state=="done":
                    costo += lin.price_unit_it * lin.quantity_done
                    cantidad += lin.quantity_done
            price_sol = (costo / cantidad) if cantidad != 0 else 0
            tc = self.env["res.currency.rate"].sudo().search([("name","=", ((i.order_id.date_order - datetime.timedelta(hours=5)).date()) if i.order_id.date_order else False),("currency_id.name","=","USD"),("company_id","in",[False,self.env.company.id])],limit=1).sale_type
            i.cost_kardex = price_sol
            i.cost_kardex_dolar = (price_sol / tc) if tc!=0 else 0