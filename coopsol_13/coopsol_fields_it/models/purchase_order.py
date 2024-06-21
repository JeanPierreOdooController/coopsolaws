# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	contact_partner_id = fields.Many2one('res.partner',string='Contacto')
	quot_number = fields.Char(string=u'Nro Cotización Proveedor')
	contact_id = fields.Many2one('res.partner',string='Contacto')
	analytic_account_id = fields.Many2one('account.analytic.account',string=u'Cuenta Analítica')
	obs = fields.Text(string='Observaciones')
	ambassador_id = fields.Many2one('res.partner',string='Embajador')