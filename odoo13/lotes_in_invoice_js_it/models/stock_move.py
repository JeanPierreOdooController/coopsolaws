from openerp.osv import osv
import base64
from openerp import models, fields, api, exceptions, _
import csv
from tempfile import TemporaryFile
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from odoo.addons.payment.models.payment_acquirer import ValidationError

class SrockMoveIT(models.Model):
    _inherit = 'stock.move'

    tracking_it = fields.Selection(related="product_id.tracking")
    description_picking = fields.Text(compute="get_descripcion_it")
    description_picking_extra = fields.Text(string="Descripcion Adicional")

    def get_descripcion_it(self):
        for record in self:

            product_name = str(record.product_id.name)
            if record.sale_line_id:
                if record.sale_line_id.product_id:
                    if record.sale_line_id.product_id.id == record.product_id.id:
                        product_name = record.sale_line_id.name

            tracking_init = record.tracking_it
            tracking = record.tracking_it

            if tracking == 'serial':
                tracking = 'Series:'

            if tracking  == 'lot':
                tracking = 'Lotes:'

            if tracking == 'none':
                tracking = ''
            #sanitario = str(record.product_id.reg_san) if record.product_id.reg_san else ' '
            #texto = product_name + '  ' + sanitario + '  ' + tracking + "\n"

            texto = product_name
            texto2 = ''
            c = 0
            for l in record.move_line_ids:
                if l.lot_id and tracking_init in  ['lot','serial']:

                    if l.lot_id.name:
                        c += 1
                        fv = str(l.lot_id.life_date.strftime('%Y-%m-%d')) if l.lot_id.life_date else None
                        if fv:
                            fv = " F.V.: " + fv
                        else:
                            fv= ''

                    texto2 += str(l.lot_id.name) + "  Cant: " + str(l.qty_done) + fv + "\n"
                    c += 1
            if c > 0:
                texto += '  ' + tracking + "\n"
                texto += texto2


            if record.description_picking_extra:
                texto += record.description_picking_extra
            record.description_picking = texto


