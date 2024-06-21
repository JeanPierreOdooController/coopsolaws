# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountJournalBook(models.Model):
	_name = 'account.journal.book'
	_description = 'Account Journal Book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(12,2))
	moneda = fields.Char(string='Mon', size=5)
	tc = fields.Float(string='TC', digits=(12,4))
	importe_me = fields.Float(string='Importe Me',digits=(64,2))
	code_cta_analitica = fields.Char(string='Cta Analítica')
	glosa = fields.Char(string='Glosa',size=50)
	td_partner = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD',size=50)
	nro_comprobante = fields.Char(string=u'Nro Comp', size=50)
	fecha_doc = fields.Date(string=u'Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
	col_reg = fields.Char(string='Col Reg', size=50)
	monto_reg = fields.Float(string='Monto Reg',digits=(12,3))
	medio_pago = fields.Char(string='Medio Pago')
	ple_diario = fields.Char(string='PLE Diario')
	ple_compras = fields.Char(string='PLE Compras')
	ple_ventas = fields.Char(string='PLE Ventas')
	registro = fields.Char(string='Registro')
	analytic_tag_names = fields.Text(string='Etiquetas Analiticas')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				
			SELECT row_number() OVER () AS id, T.* FROM (SELECT
			vst1.periodo,vst1.fecha,vst1.libro,vst1.voucher,
			vst1.cuenta,vst1.debe,vst1.haber,vst1.balance,
			vst1.moneda,vst1.tc,vst1.importe_me,vst1.code_cta_analitica,
			vst1.glosa,vst1.td_partner,vst1.doc_partner,vst1.partner,
			vst1.td_sunat,vst1.nro_comprobante,vst1.fecha_doc,vst1.fecha_ven,
			vst1.col_reg,vst1.monto_reg,vst1.medio_pago,vst1.ple_diario,
			vst1.ple_compras,vst1.ple_ventas,vst1.registro, array_to_string(vst1.analytic_tag_names,',','*') as analytic_tag_names
			FROM vst_diariog vst1 LIMIT 1)T
			)''' % (self._table,)
		)