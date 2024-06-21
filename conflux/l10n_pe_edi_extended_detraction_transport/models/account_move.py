# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
import logging
log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    l10n_pe_dte_dettran_origin_address_id = fields.Many2one('res.partner', string='Dirección de origen')
    l10n_pe_dte_dettran_delivery_address_id = fields.Many2one('res.partner', string='Dirección de llegada')
    l10n_pe_dte_dettran_val_ref_serv_trans = fields.Float('Valor Referencial', digits=(9,2))
    l10n_pe_dte_dettran_val_ref_carga_efec = fields.Float('Carga Efectiva (TM)', digits=(9,3))
    l10n_pe_dte_dettran_val_ref_carga_util = fields.Float('Carga Util (TM)', digits=(9,3))
    l10n_pe_dte_dettran_detalle_viaje = fields.Char('Detalle de Viaje')

    def _l10n_pe_prepare_dte(self):
        res = super(AccountInvoice, self)._l10n_pe_prepare_dte()
        if self.l10n_pe_dte_dettran_origin_address_id:
            res["detraction_origin_address_street"]=(self.l10n_pe_dte_dettran_origin_address_id.street_name or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.street_number and (' ' + self.l10n_pe_dte_dettran_origin_address_id.street_number) or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.street_number2 and (' ' + self.l10n_pe_dte_dettran_origin_address_id.street_number2) or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.street2 and (' ' + self.l10n_pe_dte_dettran_origin_address_id.street2) or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.l10n_pe_district and ', ' + self.l10n_pe_dte_dettran_origin_address_id.l10n_pe_district.name or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.city_id and ', ' + self.l10n_pe_dte_dettran_origin_address_id.city_id.name or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.state_id and ', ' + self.l10n_pe_dte_dettran_origin_address_id.state_id.name or '') \
                    + (self.l10n_pe_dte_dettran_origin_address_id.country_id and ', ' + self.l10n_pe_dte_dettran_origin_address_id.country_id.name or '')
            res["detraction_origin_address_zip"]=self.l10n_pe_dte_dettran_origin_address_id.zip
        if self.l10n_pe_dte_dettran_delivery_address_id:
            res["detraction_delivery_address_street"]=(self.l10n_pe_dte_dettran_delivery_address_id.street_name or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.street_number and (' ' + self.l10n_pe_dte_dettran_delivery_address_id.street_number) or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.street_number2 and (' ' + self.l10n_pe_dte_dettran_delivery_address_id.street_number2) or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.street2 and (' ' + self.l10n_pe_dte_dettran_delivery_address_id.street2) or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.l10n_pe_district and ', ' + self.l10n_pe_dte_dettran_delivery_address_id.l10n_pe_district.name or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.city_id and ', ' + self.l10n_pe_dte_dettran_delivery_address_id.city_id.name or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.state_id and ', ' + self.l10n_pe_dte_dettran_delivery_address_id.state_id.name or '') \
                    + (self.l10n_pe_dte_dettran_delivery_address_id.country_id and ', ' + self.l10n_pe_dte_dettran_delivery_address_id.country_id.name or '')
            res["detraction_delivery_address_zip"]=self.l10n_pe_dte_dettran_delivery_address_id.zip

        if self.l10n_pe_dte_dettran_val_ref_serv_trans:
            res["detraction_val_ref_serv_trans"]=self.l10n_pe_dte_dettran_val_ref_serv_trans
        if self.l10n_pe_dte_dettran_val_ref_carga_efec:
            res["detraction_val_ref_carga_efec"]=self.l10n_pe_dte_dettran_val_ref_carga_efec
        if self.l10n_pe_dte_dettran_val_ref_carga_util:
            res["detraction_val_ref_carga_util"]=self.l10n_pe_dte_dettran_val_ref_carga_util
        if self.l10n_pe_dte_dettran_detalle_viaje:
            res["detraction_detalle_viaje"]=self.l10n_pe_dte_dettran_detalle_viaje
        return res
