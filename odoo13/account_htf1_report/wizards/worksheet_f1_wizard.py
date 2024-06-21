# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class WorksheetF1Wizard(models.TransientModel):
	_name = 'worksheet.f1.wizard'
	_description = 'Worksheet F1 Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='excel',string=u'Mostrar en', required=True)
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)
	show_account_entries = fields.Boolean(string='Mostrar Rubros de Cuenta',default=False)
	level = fields.Selection([('balance','Balance'),('register','Registro')],default='balance',string='Nivel',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def _get_f1_register_sql(self):
		if self.currency == 'pen':
			sql = """
			CREATE OR REPLACE VIEW f1_register AS
			(
				SELECT row_number() OVER () AS id,
				'{period_from}' as period_from,
				'{period_to}' as period_to,
				* FROM (
				SELECT mayor, cuenta, nomenclatura, debe, haber, saldo_deudor, saldo_acreedor, activo, pasivo, perdinat, ganannat, perdifun, gananfun, rubro
				FROM get_f1_register('{period_from}','{period_to}',{company},'pen')
				UNION ALL
				SELECT 
				null::text as mayor,
				null::character varying as cuenta,
				'SUMAS'::text as nomenclatura,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldo_deudor) as saldo_deudor,
				sum(saldo_acreedor) as saldo_acreedor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdinat) as perdinat,
				sum(ganannat) as ganannat,
				sum(perdifun) as perdifun,
				sum(gananfun) as gananfun,
				null::text as rubro
				FROM get_f1_register('{period_from}','{period_to}',{company},'pen')
				UNION ALL
				SELECT 
				null::text as mayor,
				null::character varying as cuenta,
				'UTILIDAD O PERDIDA'::text as nomenclatura,
				case
					when sum(debe) < sum(haber)
					then sum(haber) - sum(debe)
					else 0
				end as debe,
				case
					when sum(debe) > sum(haber)
					then sum(debe) - sum(haber) 
					else 0
				end as haber,
				case
					when sum(saldo_deudor) < sum(saldo_acreedor)
					then sum(saldo_acreedor) - sum(saldo_deudor)
					else 0
				end as saldo_deudor,
				case
					when sum(saldo_deudor) > sum(saldo_acreedor)
					then sum(saldo_deudor) - sum(saldo_acreedor)
					else 0
				end as saldo_acreedor,
				case
					when sum(activo) < sum(pasivo)
					then sum(pasivo) - sum(activo)
					else 0
				end as activo,
				case
					when sum(activo) > sum(pasivo)
					then sum(activo) - sum(pasivo)
					else 0
				end as pasivo,
				case
					when sum(perdinat) < sum(ganannat)
					then sum(ganannat) - sum(perdinat)
					else 0
				end as perdinat,
				case
					when sum(perdinat) > sum(ganannat)
					then sum(perdinat) - sum(ganannat)
					else 0
				end as ganannat,
				case
					when sum(perdifun) < sum(gananfun)
					then sum(gananfun) - sum(perdifun)
					else 0
				end as perdifun,
				case
					when sum(perdifun) > sum(gananfun)
					then sum(perdifun) - sum(gananfun)
					else 0
				end as gananfun,
				null::text as rubro
				FROM get_f1_register('{period_from}','{period_to}',{company},'pen')
					)T
			)
			""".format(
					period_from = self.period_from.code,
					period_to = self.period_to.code,
					company = self.company_id.id
				)
		else:
			sql = """
			CREATE OR REPLACE VIEW f1_register AS
			(
			SELECT row_number() OVER () AS id,
				'{period_from}' as period_from,
				'{period_to}' as period_to,
				* FROM 
			(SELECT TF.mayor, TF.cuenta, TF.nomenclatura,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END AS debe,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END AS haber,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.saldo_deudor/TF.compra,2)
ELSE round(TF.saldo_deudor/TF.venta,2) END AS saldo_deudor,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.saldo_acreedor/TF.compra,2)
ELSE round(TF.saldo_acreedor/TF.venta,2) END AS saldo_acreedor,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.activo/TF.compra,2)
ELSE round(TF.activo/TF.venta,2) END AS activo,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.pasivo/TF.compra,2)
ELSE round(TF.pasivo/TF.venta,2) END AS pasivo,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.perdinat/TF.compra,2)
ELSE round(TF.perdinat/TF.venta,2) END AS perdinat,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.ganannat/TF.compra,2)
ELSE round(TF.ganannat/TF.venta,2) END AS ganannat,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.perdifun/TF.compra,2)
ELSE round(TF.perdifun/TF.venta,2) END AS perdifun,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.gananfun/TF.compra,2)
ELSE round(TF.gananfun/TF.venta,2) END AS gananfun,
TF.rubro FROM
(SELECT F1.mayor, F1.cuenta, F1.nomenclatura, F1.debe, F1.haber, F1.saldo_deudor, F1.saldo_acreedor, F1.activo, F1.pasivo, 
F1.perdinat, F1.ganannat, F1.perdifun, F1.gananfun, F1.rubro, ati.group_balance, ati.group_nature, ati.group_function,
(select exl.compra from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as compra,
(select venta from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as venta
 FROM get_f1_register((select code from account_period where id ={period_from_id} limit 1) ,(select code from account_period where id ={period_to_id} limit 1),{company},'pen') F1
LEFT JOIN account_account aa on aa.id = F1.account_id
left join account_type_it ati on ati.id = aa.account_type_it_id)TF

UNION ALL

SELECT null::text AS mayor, null::character varying AS cuenta, 'Diferencia TC'::text  AS nomenclatura,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS debe,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS haber,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS saldo_deudor,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS saldo_acreedor,

0.00 AS activo,
0.00 AS pasivo,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS perdinat,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS ganannat,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS perdifun,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS gananfun,
'' AS rubro  FROM
(SELECT F1.mayor, F1.cuenta, F1.nomenclatura, F1.debe, F1.haber, F1.saldo_deudor, F1.saldo_acreedor, F1.activo, F1.pasivo, 
F1.perdinat, F1.ganannat, F1.perdifun, F1.gananfun, F1.rubro, ati.group_balance, ati.group_nature, ati.group_function,
(select exl.compra from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as compra,
(select venta from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as venta
 FROM get_f1_register((select code from account_period where id ={period_from_id} limit 1) ,(select code from account_period where id ={period_to_id} limit 1),{company},'pen') F1
LEFT JOIN account_account aa on aa.id = F1.account_id
left join account_type_it ati on ati.id = aa.account_type_it_id)TF

UNION ALL

SELECT null::text AS mayor, null::character varying AS cuenta, 'SUMAS'::text AS nomenclatura,
SUM(GL.debe), SUM(GL.haber), SUM(GL.saldo_deudor), SUM(GL.saldo_acreedor), SUM(GL.activo), SUM(GL.pasivo), 
SUM(GL.perdinat), SUM(GL.ganannat), SUM(GL.perdifun), SUM(GL.gananfun), '' AS rubro FROM 
(SELECT TF.mayor, TF.cuenta, TF.nomenclatura,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END AS debe,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END AS haber,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.saldo_deudor/TF.compra,2)
ELSE round(TF.saldo_deudor/TF.venta,2) END AS saldo_deudor,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.saldo_acreedor/TF.compra,2)
ELSE round(TF.saldo_acreedor/TF.venta,2) END AS saldo_acreedor,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.activo/TF.compra,2)
ELSE round(TF.activo/TF.venta,2) END AS activo,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.pasivo/TF.compra,2)
ELSE round(TF.pasivo/TF.venta,2) END AS pasivo,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.perdinat/TF.compra,2)
ELSE round(TF.perdinat/TF.venta,2) END AS perdinat,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.ganannat/TF.compra,2)
ELSE round(TF.ganannat/TF.venta,2) END AS ganannat,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.perdifun/TF.compra,2)
ELSE round(TF.perdifun/TF.venta,2) END AS perdifun,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.gananfun/TF.compra,2)
ELSE round(TF.gananfun/TF.venta,2) END AS gananfun,
TF.rubro FROM
(SELECT F1.mayor, F1.cuenta, F1.nomenclatura, F1.debe, F1.haber, F1.saldo_deudor, F1.saldo_acreedor, F1.activo, F1.pasivo, 
F1.perdinat, F1.ganannat, F1.perdifun, F1.gananfun, F1.rubro, ati.group_balance, ati.group_nature, ati.group_function,
(select exl.compra from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as compra,
(select venta from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as venta
 FROM get_f1_register((select code from account_period where id ={period_from_id} limit 1) ,(select code from account_period where id ={period_to_id} limit 1),{company},'pen') F1
LEFT JOIN account_account aa on aa.id = F1.account_id
left join account_type_it ati on ati.id = aa.account_type_it_id)TF

UNION ALL

SELECT null::text AS mayor, null::character varying AS cuenta, 'Diferencia TC'::text AS nomenclatura,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS debe,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS haber,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS saldo_deudor,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS saldo_acreedor,

0.00 AS activo,
0.00 AS pasivo,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS perdinat,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS ganannat,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS perdifun,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS gananfun,
'' AS rubro FROM
(SELECT F1.mayor, F1.cuenta, F1.nomenclatura, F1.debe, F1.haber, F1.saldo_deudor, F1.saldo_acreedor, F1.activo, F1.pasivo, 
F1.perdinat, F1.ganannat, F1.perdifun, F1.gananfun, F1.rubro, ati.group_balance, ati.group_nature, ati.group_function,
(select exl.compra from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as compra,
(select venta from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as venta
 FROM get_f1_register((select code from account_period where id ={period_from_id} limit 1) ,(select code from account_period where id ={period_to_id} limit 1),{company},'pen') F1
LEFT JOIN account_account aa on aa.id = F1.account_id
left join account_type_it ati on ati.id = aa.account_type_it_id)TF)GL

UNION ALL
---
SELECT null::text AS mayor, null::character varying AS cuenta, 'RESULTADO DEL PERIODO'::text AS nomenclatura,
0.00 as debe, 0.00 as haber, 0.00 as saldo_deudor, 0.00 as saldo_acreedor,
CASE WHEN SUM(GLEN.activo) > SUM(GLEN.pasivo) THEN 0.00 ELSE SUM(GLEN.pasivo) - SUM(GLEN.activo) END AS activo,
CASE WHEN SUM(GLEN.pasivo) > SUM(GLEN.activo) THEN 0.00 ELSE SUM(GLEN.activo) - SUM(GLEN.pasivo) END AS pasivo,

CASE WHEN SUM(GLEN.perdinat) > SUM(GLEN.ganannat) THEN 0.00 ELSE SUM(GLEN.ganannat) - SUM(GLEN.perdinat) END AS perdinat,
CASE WHEN SUM(GLEN.ganannat) > SUM(GLEN.perdinat) THEN 0.00 ELSE SUM(GLEN.perdinat) - SUM(GLEN.ganannat) END AS ganannat,

CASE WHEN SUM(GLEN.perdifun) > SUM(GLEN.gananfun) THEN 0.00 ELSE SUM(GLEN.gananfun) - SUM(GLEN.perdifun) END AS perdifun,
CASE WHEN SUM(GLEN.gananfun) > SUM(GLEN.perdifun) THEN 0.00 ELSE SUM(GLEN.perdifun) - SUM(GLEN.gananfun) END AS gananfun,
'' AS rubro FROM (
SELECT TF.mayor, TF.cuenta, TF.nomenclatura,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END AS debe,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END AS haber,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.saldo_deudor/TF.compra,2)
ELSE round(TF.saldo_deudor/TF.venta,2) END AS saldo_deudor,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.saldo_acreedor/TF.compra,2)
ELSE round(TF.saldo_acreedor/TF.venta,2) END AS saldo_acreedor,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.activo/TF.compra,2)
ELSE round(TF.activo/TF.venta,2) END AS activo,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.pasivo/TF.compra,2)
ELSE round(TF.pasivo/TF.venta,2) END AS pasivo,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.perdinat/TF.compra,2)
ELSE round(TF.perdinat/TF.venta,2) END AS perdinat,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.ganannat/TF.compra,2)
ELSE round(TF.ganannat/TF.venta,2) END AS ganannat,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.perdifun/TF.compra,2)
ELSE round(TF.perdifun/TF.venta,2) END AS perdifun,
CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.gananfun/TF.compra,2)
ELSE round(TF.gananfun/TF.venta,2) END AS gananfun,
TF.rubro FROM
(SELECT F1.mayor, F1.cuenta, F1.nomenclatura, F1.debe, F1.haber, F1.saldo_deudor, F1.saldo_acreedor, F1.activo, F1.pasivo, 
F1.perdinat, F1.ganannat, F1.perdifun, F1.gananfun, F1.rubro, ati.group_balance, ati.group_nature, ati.group_function,
(select exl.compra from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as compra,
(select venta from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as venta
 FROM get_f1_register((select code from account_period where id ={period_from_id} limit 1) ,(select code from account_period where id ={period_to_id} limit 1),{company},'pen') F1
LEFT JOIN account_account aa on aa.id = F1.account_id
left join account_type_it ati on ati.id = aa.account_type_it_id)TF

UNION ALL

SELECT null::text AS mayor, null::character varying AS cuenta, 'Diferencia TC'::text AS nomenclatura,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS debe,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS haber,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS saldo_deudor,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS saldo_acreedor,

0.00 AS activo,
0.00 AS pasivo,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS perdinat,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS ganannat,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN 0.00 ELSE SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) END AS perdifun,

CASE WHEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) > SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) THEN SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.debe/TF.compra,2)
ELSE round(TF.debe/TF.venta,2) END) - SUM(CASE WHEN left(TF.cuenta,1) in ('0','1','2','3') THEN round(TF.haber/TF.compra,2)
ELSE round(TF.haber/TF.venta,2) END) ELSE 0.00 END AS gananfun,
'' AS rubro  FROM
(SELECT F1.mayor, F1.cuenta, F1.nomenclatura, F1.debe, F1.haber, F1.saldo_deudor, F1.saldo_acreedor, F1.activo, F1.pasivo, 
F1.perdinat, F1.ganannat, F1.perdifun, F1.gananfun, F1.rubro, ati.group_balance, ati.group_nature, ati.group_function,
(select exl.compra from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as compra,
(select venta from exchange_diff_config_line exl 
left join exchange_diff_config ex on ex.id = exl.line_id where ex.company_id = {company} and exl.period_id = {period_to_id} limit 1) as venta
 FROM get_f1_register((select code from account_period where id ={period_from_id} limit 1) ,(select code from account_period where id ={period_to_id} limit 1),{company},'pen') F1
LEFT JOIN account_account aa on aa.id = F1.account_id
left join account_type_it ati on ati.id = aa.account_type_it_id)TF
)GLEN)USD )
			""".format(
				period_from = self.period_from.code,
				period_to = self.period_to.code,
				period_from_id = self.period_from.id,
				period_to_id = self.period_to.id,
				company = self.company_id.id
			)
		return sql

	def _get_f1_balance_sql(self):
		sql = """
		CREATE OR REPLACE VIEW f1_balance AS 
		(
			SELECT row_number() OVER () AS id,
			'{period_from}' as period_from,
			'{period_to}' as period_to, * FROM (
			SELECT *
			FROM get_f1_balance('{period_from}','{period_to}',{company},'{currency}')
			UNION ALL
			SELECT 
			null::text as mayor,
			'SUMAS'::text as nomenclatura,
			sum(debe) as debe,
			sum(haber) as haber,
			sum(saldo_deudor) as saldo_deudor,
			sum(saldo_acreedor) as saldo_acreedor,
			sum(activo) as activo,
			sum(pasivo) as pasivo,
			sum(perdinat) as perdinat,
			sum(ganannat) as ganannat,
			sum(perdifun) as perdifun,
			sum(gananfun) as gananfun
			FROM get_f1_balance('{period_from}','{period_to}',{company},'{currency}')
			UNION ALL
			SELECT 
			null::text as mayor,
			'UTILIDAD O PERDIDA'::text as nomenclatura,
			case
				when sum(debe) < sum(haber)
				then sum(haber) - sum(debe)
				else 0
			end as debe,
			case
				when sum(debe) > sum(haber)
				then sum(debe) - sum(haber) 
				else 0
			end as haber,
			case
				when sum(saldo_deudor) < sum(saldo_acreedor)
				then sum(saldo_acreedor) - sum(saldo_deudor)
				else 0
			end as saldo_deudor,
			case
				when sum(saldo_deudor) > sum(saldo_acreedor)
				then sum(saldo_deudor) - sum(saldo_acreedor)
				else 0
			end as saldo_acreedor,
			case
				when sum(activo) < sum(pasivo)
				then sum(pasivo) - sum(activo)
				else 0
			end as activo,
			case
				when sum(activo) > sum(pasivo)
				then sum(activo) - sum(pasivo)
				else 0
			end as pasivo,
			case
				when sum(perdinat) < sum(ganannat)
				then sum(ganannat) - sum(perdinat)
				else 0
			end as perdinat,
			case
				when sum(perdinat) > sum(ganannat)
				then sum(perdinat) - sum(ganannat)
				else 0
			end as ganannat,
			case
				when sum(perdifun) < sum(gananfun)
				then sum(gananfun) - sum(perdifun)
				else 0
			end as perdifun,
			case
				when sum(perdifun) > sum(gananfun)
				then sum(perdifun) - sum(gananfun)
				else 0
			end as gananfun
			FROM get_f1_balance('{period_from}','{period_to}',{company},'{currency}')
				)T
		)
		""".format(
				period_from = self.period_from.code,
				period_to = self.period_to.code,
				company = self.company_id.id,
				currency = self.currency
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_f1_register_sql())
		if self.level == 'balance':
			self._cr.execute(self._get_f1_balance_sql())
		if self.type_show == 'pantalla':
			if self.level == 'register':
				return self.get_window_f1_register()
			else:
				return self.get_window_f1_balance()
		else:
			if self.level == 'register':
				return self.get_excel_f1_register()
			else:
				return self.get_excel_f1_balance()

	def get_window_f1_register(self):
		if self.show_account_entries:
			view = self.env.ref('account_htf1_report.view_f1_register_tree_true').id
		else:
			view = self.env.ref('account_htf1_report.view_f1_register_tree').id
		return {
			'name': 'Hoja de Trabajo F1 - Registro',
			'type': 'ir.actions.act_window',
			'res_model': 'f1.register',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_window_f1_balance(self):
		view = self.env.ref('account_htf1_report.view_f1_balance_tree').id
		return {
			'name': 'Hoja de Trabajo F1 - Balance',
			'type': 'ir.actions.act_window',
			'res_model': 'f1.balance',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_excel_f1_register(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Hoja_Trabajo_F1.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Hoja de Trabajo F1")
		worksheet.set_tab_color('blue')

		HEADERS = ['MAYOR','CUENTA','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR',
				   'ACTIVO','PASIVO','PERDINAT','GANANNAT','PERDIFUN','GANANFUN']
		if self.show_account_entries:
			HEADERS.append('RUBRO ESTADO FINANCIERO')
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		total = len(self.env['f1.register'].search([])) - 2
		for c,line in enumerate(self.env['f1.register'].search([]),1):
			worksheet.write(x,0,line.mayor if line.mayor else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.nomenclatura if line.nomenclatura else '',formats['especial1'] if c <= total else formats['boldbord'])
			worksheet.write(x,3,line.debe if line.debe else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,4,line.haber if line.haber else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,5,line.saldo_deudor if line.saldo_deudor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,6,line.saldo_acreedor if line.saldo_acreedor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,7,line.activo if line.activo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,8,line.pasivo if line.pasivo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,9,line.perdinat if line.perdinat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,10,line.ganannat if line.ganannat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,11,line.perdifun if line.perdifun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,12,line.gananfun if line.gananfun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			if self.show_account_entries:
				worksheet.write(x,13,line.rubro if line.rubro else '',formats['especial1'])
			x += 1

		widths = [7,9,40,10,10,10,10,10,10,10,10,10,10,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Hoja_Trabajo_F1.xlsx', 'rb')
		return self.env['popup.it'].get_file('Hoja_Trabajo_F1_Nivel_Registro.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_f1_balance(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Hoja_Trabajo_F1.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Hoja de Trabajo F1")
		worksheet.set_tab_color('blue')

		HEADERS = ['MAYOR','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR',
				   'ACTIVO','PASIVO','PERDINAT','GANANNAT','PERDIFUN','GANANFUN']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		total = len(self.env['f1.balance'].search([])) - 2
		for c,line in enumerate(self.env['f1.balance'].search([]),1):
			worksheet.write(x,0,line.mayor if line.mayor else '',formats['especial1'])
			worksheet.write(x,1,line.nomenclatura if line.nomenclatura else '',formats['especial1'] if c <= total else formats['boldbord'])
			worksheet.write(x,2,line.debe if line.debe else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,3,line.haber if line.haber else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,4,line.saldo_deudor if line.saldo_deudor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,5,line.saldo_acreedor if line.saldo_acreedor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,6,line.activo if line.activo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,7,line.pasivo if line.pasivo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,8,line.perdinat if line.perdinat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,9,line.ganannat if line.ganannat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,10,line.perdifun if line.perdifun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,11,line.gananfun if line.gananfun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			x += 1

		widths = [7,40,10,10,10,10,10,10,10,10,10,10,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Hoja_Trabajo_F1.xlsx', 'rb')
		return self.env['popup.it'].get_file('Hoja_Trabajo_F1_Nivel_Balance.xlsx',base64.encodestring(b''.join(f.readlines())))