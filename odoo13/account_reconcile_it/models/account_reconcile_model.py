# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountReconcileModel(models.Model):
	_inherit = 'account.reconcile.model'

	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	nro_comp = fields.Char(string=u'N° Comprobante',size=40)

	def _prepare_reconciliation(self, st_line, move_lines=None, partner=None):
		data = super(AccountReconcileModel,self)._prepare_reconciliation(st_line, move_lines, partner)
		if move_lines:
			for aml_dict in data['counterpart_aml_dicts']:
				if aml_dict['move_line'].type_document_id:
					aml_dict['type_document_id'] = aml_dict['move_line'].type_document_id.id
				if aml_dict['move_line'].nro_comp:
					aml_dict['nro_comp'] = aml_dict['move_line'].nro_comp

		return data

	def _get_write_off_move_lines_dict(self, st_line, move_lines=None):
		ret = super(AccountReconcileModel,self)._get_write_off_move_lines_dict(st_line,move_lines=move_lines)
		for line in ret:
			if line['account_id'] == self.account_id.id:
				line['type_document_id'] = self.type_document_id.id
				line['nro_comp'] = self.nro_comp
		return ret