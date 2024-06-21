# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountExchangeDocumentBook(models.Model):
	_name = 'account.exchange.document.book'
	_description = 'Account Exchange Document Book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	cuenta = fields.Char(string='Cuenta')
	partner = fields.Char(string='Partner', size=150)
	td_sunat = fields.Char(string='TD', size=3)
	nro_comprobante = fields.Char(string='Nro. Comprobante', size=3)
	debe = fields.Float(string='Debe',digits=(12,2))
	haber = fields.Float(string='Haber',digits=(12,2))
	saldomn = fields.Float(string='Saldo MN',digits=(12,2))
	saldome = fields.Float(string='Saldo ME',digits=(12,2))
	tc = fields.Float(string='TC',digits=(12,3))
	saldo_act = fields.Float(string='Saldo Act.',digits=(12,2))
	diferencia = fields.Float(string='Diferencia',digits=(12,2))
	cuenta_diferencia = fields.Char(string='Cuenta Diferencia')
	account_id = fields.Many2one('account.account',string='Cuenta ID')
	partner_id = fields.Many2one('res.partner',string='Partner ID')
	period_id = fields.Many2one('account.period',string='Periodo ID')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT 
				row_number() OVER () AS id,
				''::text as periodo,
				''::character varying(64) as cuenta,
				''::character varying as partner,
				vst.td_sunat,
				vst.nro_comprobante,
				vst.debe,
				vst.haber,
				vst.saldomn,
				vst.saldome,
				vst.tc,
				vst.saldo_act,
				vst.diferencia,
				''::character varying(64) as cuenta_diferencia,
				vst.account_id,
				vst.partner as partner_id,
				0::integer as period_id
				FROM get_saldos_me_documento_final('2019','201901',1) vst limit 1
			
			)''' % (self._table,)
		)