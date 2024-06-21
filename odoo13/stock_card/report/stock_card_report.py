# -*- coding: utf-8 -*-
# Copyright (C) 2018-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

import xlsxwriter
from odoo import api, fields, models
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class AccountXlsx(models.AbstractModel):
    _name = 'report.stock_card.card_report_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_lines(self, obj):
        lines = []
        domain = [
            ('state', '=', 'done'),
            ('product_id', '=', obj.product_id.id),
            '|',
            ('location_id', '=', obj.location_id.id),
            ('location_dest_id', '=', obj.location_id.id),
            ('date', '>=', obj.start_date),
            ('date', '<=', obj.end_date),
        ]
        sale_order = self.env['stock.move'].search(domain, order='date desc')

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        lang = self._context.get("lang")
        record_lang = self.env["res.lang"].search([("code", "=", lang)], limit=1)
      
        for value in sale_order:
       
            qty_in = 0
            qty_out = 0
            reference = ""
            ot = ""
            if obj.location_id.id == value.location_dest_id.id:
                qty_in = value.product_qty
            else:
                qty_out = value.product_qty
            if not value.picking_id:
                reference = ""
            else:
                reference = value.picking_id.name

            vals = {
                'ref': reference,
                'product_id': value.product_id.id,
                'product': value.product_id.display_name,
                'location_id': value.location_dest_id.id,
                'origen': value.location_id.name,
                'destino': value.location_dest_id.name,
                'date': value.date, #pytz.UTC.localize(datetime.strptime(value.date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz),
                'qty_in': qty_in,
                'qty_out': qty_out,
                'saldo': value.product_id.with_context({'to_date': value.date,'location' : obj.location_id.id}).qty_available,
                'ot': (value.picking_id.ot_id.name or value.picking_id.x_ot or "")
            }
            lines.append(vals)
        return lines

    def generate_xlsx_report(self, workbook, data, wizard_obj):
        for obj in wizard_obj:
            lines = self.get_lines(obj)
            worksheet = workbook.add_worksheet('Report')
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            text = workbook.add_format({'font_size': 12, 'align': 'center'})
            text1 = workbook.add_format({'font_size': 12})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})
            worksheet.set_column(0, 0, 15)
            worksheet.set_column(1, 2, 25)
            worksheet.set_column(3, 3, 15)
            worksheet.set_column(4, 4, 15)
            worksheet.write('A1', 'Producto:', bold)
            worksheet.write('B1', lines[0]['product'], text1)
            worksheet.write('A2', 'Desde:', bold)
            worksheet.write('B2', datetime.strptime(obj.start_date, '%Y-%m-%d'), date_format)
            worksheet.write('C2', 'Hasta:', bold)
            worksheet.write('D2', datetime.strptime(obj.end_date, '%Y-%m-%d'), date_format)
            worksheet.write('A3', 'Referencia', bold)
            worksheet.write('B3', 'Fecha', bold)
            worksheet.write('C3', 'Ingresos', bold)
            worksheet.write('D3', 'Salidas', bold)
            worksheet.write('E3', 'origen', bold)
            worksheet.write('F3', 'destino', bold)
            worksheet.write('G3', 'Saldo', bold)
            worksheet.write('H3', 'OT', bold)
            row = 3
            col = 0

            for res in lines:
                date_time = datetime.strptime(res['date'],'%Y-%m-%d %H:%M:%S')
                worksheet.write(row, col, res['ref'], text)
                worksheet.write(row, col + 1, date_time, date_format)
                worksheet.write(row, col + 2, res['qty_in'], text)
                worksheet.write(row, col + 3, res['qty_out'], text)
                worksheet.write(row, col + 4, res['origen'], text)
                worksheet.write(row, col + 5, res['destino'], text)
                worksheet.write(row, col + 6, res['saldo'], text)
                worksheet.write(row, col + 7, res['ot'], text)
                row = row + 1
            worksheet.add_table('A4:H'+str(row), {'autofilter': False,'header_row': False})
