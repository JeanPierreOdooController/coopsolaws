# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class SaleAnalysisWizard(models.TransientModel):
    _name = 'sale.analysis.wizard'

    name = fields.Char()
    company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
    fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
    period_start = fields.Many2one('account.period',string='Periodo Inicial',required=True)
    period_end = fields.Many2one('account.period',string='Periodo Final',required=True)

    @api.onchange('company_id')
    def get_fiscal_year(self):
        if self.company_id:
            fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
            if fiscal_year:
                self.fiscal_year_id = fiscal_year.id
            else:
                raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

    def get_report(self):
        self.env.cr.execute("""
            CREATE OR REPLACE view sale_analysis_book as ("""+self._get_sql()+""")""")
        '''
        for l in self.env['sale.analysis.book'].search([]):
            order = self.env['sale.order'].search([('company_id','=',l.move_id.company_id.id),('name','=',l.move_id.invoice_origin)])
            if order:
                if order.team_id:
                    #self.env.cr.execute("UPDATE sale_analysis_book SET team_vendor = '{}'  WHERE  id = {}".format(str(order.team_id.name),l.id))
                    l.team_vendor = order.team_id.name
        '''
        return {
            'name': 'Analisis de Ventas',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.analysis.book',
            'view_mode': 'tree,pivot,graph',
            'view_type': 'form',
        }

    def _get_sql(self):
        sql_filter = ""
        if not self.env.user.has_group('sale_analysis_it.group_sale_analysis_it'):
            sql_filter = " and rup.name = '%s'" % (self.env.user.name)
        sql = """
                select row_number() OVER () AS id, 
                T.* from(
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
                '-' as  team_vendor,
                albaran.precio_unitario as standard_price,
                case when coalesce(albaran.cantidadlineas,0) > 1 and pt.tracking = 'none' then true else false end as flag
                from vst_diariog vst
                left join account_move am on am.id = vst.move_id
                left join account_move_line aml on aml.id = vst.move_line_id
                left join ( 
                        select sm.invoice_id as am_id,sm.product_id, avg(price_unit_it) as precio_unitario,count(*) as cantidadlineas  from 
                        stock_picking sp 
                        join stock_move sm on sm.picking_id = sp.id
                        join stock_location sl on sl.id = sm.location_dest_id
                        where sl.usage = 'customer'
                        group by sm.invoice_id,sm.product_id
                 ) as albaran on albaran.am_id = am.id and albaran.product_id = aml.product_id
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
                where (vst.periodo::int between %s and %s) and left(vst.cuenta,2)='70'
                and vst.company_id = %s
                %s
                )T
        """ % (self.period_start.code,
        self.period_end.code,
        str(self.company_id.id),
        sql_filter)

        return sql