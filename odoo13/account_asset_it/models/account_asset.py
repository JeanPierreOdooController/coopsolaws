from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAsset(models.Model):
	_inherit = 'account.asset'

	partner_id_it = fields.Many2one('res.partner', string='Socio', copy=False)
	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento', copy=False)
	nro_comp = fields.Char(string='Nro Comprobante', copy=False)

	def action_copy_comprobante(self):
		for asset in self:
			for move in asset.depreciation_move_ids:
				for line in move.line_ids:
					line.partner_id = asset.partner_id_it.id
					line.type_document_id = asset.type_document_id.id
					line.nro_comp = asset.nro_comp

		return self.env['popup.it'].get_message('Se copiaron correctamente los datos.')
	
	def action_update_amount(self):
		for asset in self:
			asset._compute_book_value()
			asset._compute_value()

		return self.env['popup.it'].get_message('Se actualizaron correctamente los datos.')