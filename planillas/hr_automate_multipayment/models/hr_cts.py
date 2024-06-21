# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class HrCts(models.Model):
    _inherit = 'hr.cts'

    txt_generated = fields.Boolean(string='Txt Generado', default=False)


class HrCtsLine(models.Model):
    _inherit = 'hr.cts.line'

    multipayment_id = fields.Many2one('hr.automate.multipayment')
    # cts_account = fields.Many2one(related='employee_id.cts_bank_account_id', string='Cuenta CTS', store=True)
    # cts_bank = fields.Many2one(related='cts_account.bank_id', string='Banco', store=True)
    sunat_code = fields.Char(related='employee_id.type_document_id.sunat_code', string="Codigo SUNAT", store=True)
    doc_number = fields.Char(related='employee_id.identification_id', string="Identificación", store=True)
