from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MessageReportCustomSale(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        if self.template_id and self.template_id.model_id and self.template_id.model_id.model == 'sale.order':
            venta = self.env['sale.order'].search( [('id', '=', self.res_id)] )
            pdf = venta.get_sale_order_print_it()
            pdf = request.env['popup.it'].search( [('id', '=', int(pdf['res_id']))] ).output_file
            pdf = base64.b64decode(pdf)
            attach = self.env['ir.attachment'].create( {
                'name': 'Reporte Venta',
                'datas': pdf
            } )
            self.attachment_ids = [attach.id]
        return super(MessageReportCustomSale, self).action_send_mail()
