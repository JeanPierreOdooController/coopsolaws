# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def create_debit(self):
        res = super(AccountDebitNote, self).create_debit()
        if res.get('res_id', False):
            debit = self.env['account.move'].browse(res.get('res_id'))
            if debit:
                debit.write({
                    'debit_note_type_id': self.env['einvoice.catalog.10'].search([('code','=', self.l10n_pe_dte_debit_note_type or '01')])[0].id,
                    'doc_invoice_relac': [(0, 0, {
                        'type_document_id': debit.debit_origin_id.type_document_id.id,
                        'date': debit.debit_origin_id.invoice_date,
                        'nro_comprobante': debit.debit_origin_id.ref,
                        'amount_currency': debit.debit_origin_id.amount_total if debit.debit_origin_id.currency_id.name != 'PEN' else 0,
                        'amount': abs(debit.debit_origin_id.amount_total_signed),
                        'bas_amount': abs(debit.debit_origin_id.amount_untaxed),
                        'tax_amount': abs(debit.debit_origin_id.amount_total_signed - debit.debit_origin_id.amount_untaxed)
                    })]
                })
        return res