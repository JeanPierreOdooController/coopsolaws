# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class DocInvoiceRelac(models.Model):
	_inherit = 'doc.invoice.relac'

	journal_id = fields.Many2one('account.journal', string='Diario', related='move_id.journal_id')
	company_id = fields.Many2one('res.company',string=u'Compañía', related='move_id.company_id')