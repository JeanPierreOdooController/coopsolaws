# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog54(models.Model):
	_name = 'einvoice.catalog.54'
	_description = 'Einvoice Catalog 54'

	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo', size=4)
	percentage = fields.Float(string='Tasa %')
	pse_code = fields.Char(string='Codigo de Facturador', size=5)

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		einvoice_ids = []
		if name:
			einvoice_ids = self._search(['|',('name', '=', name),('code','=',name)] + args, limit=limit, access_rights_uid=name_get_uid)
		if not einvoice_ids:
			einvoice_ids = self._search(['|',('name', operator, name),('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
		return self.browse(einvoice_ids).name_get()