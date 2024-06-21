# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError


class SaleAnalysisWizardPowerBy(models.TransientModel):
    _name = 'sale.analysis.wizard.powerby'

    name = fields.Char()


    def get_report(self):
        self.env.cr.execute("""CREATE OR REPLACE view sale_analysis_book_powerby as (""" + self._get_sql() + """)""")

        return {
            'name': 'Analisis de Ventas',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.analysis.book.powerby',
            'view_mode': 'tree,pivot,graph',
            'view_type': 'form',
        }

    def _get_sql(self):
        sql_filter = ""
        if not self.env.user.has_group('sale_analysis_it.group_sale_analysis_it'):
            sql_filter = " and rup.name = '%s'" % (self.env.user.name)
        sql = """ select row_number() OVER () AS id, T.* from(
        select 
        rup.name as vendedor,
        lit.name as td_partner,
        vst.doc_partner,
        vst.partner,
        vst.fecha::date as fecha,
        eic.name as td_sunat,
        vst.nro_comprobante,
        case 
            when am.invoice_payment_state = 'paid' then 'Pagado' else 'No pagado'
        end as estado_doc,
        aml.product_id as id_product,
        aml.quantity,
        case 
            when (aml.discount <> null or aml.discount <> 0) and aml.quantity <> 0 then round(aml.price_subtotal / aml.quantity :: numeric(64,2),2)
            else aml.price_unit :: numeric(64,2)
        end as price_unit ,
        rc.name as moneda,
        am.currency_rate as tc,
        aml.amount_currency*-1 as monto_dolares,
        pt.list_price,
        amr.ref as ref_doc,
        aml.product_id as product_id,
        pc.complete_name as category_name,
        pp.default_code,
        pb.name as brand,
        - vst.balance as balance,
        vst.cuenta,
        aa.name as nomenclatura,
        vst.move_id,
        '-' as  team_vendor
        from vst_diariog vst
        left join account_move am on am.id = vst.move_id
        left join account_move_line aml on aml.id = vst.move_line_id
        left join res_users ru on ru.id = am.invoice_user_id
        left join res_partner rup on rup.id = ru.partner_id
        left join product_product pp on pp.id = aml.product_id
        left join product_template pt on pt.id = pp.product_tmpl_id
        left join product_category pc on pc.id = pt.categ_id
        left join product_brand pb on pb.id = pt.product_brand_id
        left join account_account aa on aa.id = vst.account_id
        left join l10n_latam_identification_type lit on lit.code_sunat = vst.td_partner
        left join einvoice_catalog_01 eic on eic.code = vst.td_sunat
        left join res_currency rc on rc.id = am.currency_id
        left join account_move amr on amr.id = am.reversed_entry_id
        where left(vst.cuenta,2)='70'
        %s
        )T
        """ % (sql_filter)

        return sql
