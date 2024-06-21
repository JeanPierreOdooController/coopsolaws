from odoo import models, fields, api
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
import base64
from dateutil.relativedelta import relativedelta




class StockPicking(models.Model):
	_inherit = 'stock.picking'

	invoice_it_id=fields.Many2one('account.move','Factura Generada')

	def make_invoiceline_from_picking(self,lines,invoice_id):
		lineas=[]

		for l in lines:
			accounts = l.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
			
			
			line={
				'name': l.product_id.name,
				'product_id': l.product_id.id,
				'quantity': l.qty_done,
				'product_uom_id': l.product_id.uom_id.id,
				'ref': l.product_id.name,
				'partner_id': l.move_id.partner_id.id,
				'exclude_from_invoice_tab':False,
				'account_id':accounts['income'].id,
				'move_id':invoice_id,
			}
			lineret=self.env['account.move.line'].create(line)

			# price=lineret._get_computed_price_unit()
			# print(1111,price)
			# lineret.write({'price_unit':price})
			lineas.append(lineret)
		print(lineas)
		return lineas

	def make_invoice_from_picking(self):
		c=False
		for l in self:
			
			header={
				'date': fields.date.today(),
				'glosa':'Transferencia: '+l.name,
				'invoice_user_id':l.user_id.id,
				'partner_id':l.cliente.id,
				
			 }

			mycontext = self._context.copy()
			mycontext.update({
					'default_type': 'out_invoice',
				})

			c=self.env['account.move'].with_context(mycontext).create(header)
			self.make_invoiceline_from_picking(l.move_line_ids_without_package,c.id)
			l.invoice_it_id=c.id
			l.invoice_id=c.id
		if c:
			return {
					'view_mode': 'form',
					'res_model': 'account.move',
					'type': 'ir.actions.act_window',
					'res_id':c.id
				}


