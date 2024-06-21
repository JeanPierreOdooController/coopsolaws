# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO

import base64
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import openpyxl
except:
	install('openpyxl==3.0.5')

class LandedCostIt(models.Model):
	_inherit = 'landed.cost.it'

	advalorem_ids = fields.One2many('landed.cost.advalorem.line', 'landed_id',string='Advalorem')

	def calcular(self):
		t = super(LandedCostIt,self).calcular()
		for i in self.detalle_ids:
			valor_mn = sum(line['valormn'] for line in self.advalorem_ids.filtered(lambda line: line.product_id.id == i.stock_move_id.product_id.id and line.picking_id.id == i.stock_move_id.picking_id.id))
			i.flete = i.flete + valor_mn
		return t

	def get_excel_saldos(self):
		self.ensure_one()
		today = self.date_kardex.date()
		sql = sql1 = sqlsum = ""
		sql2 = """valor_p + valormn """
		sql3 = """ valormn """
		for elem in self.env['landed.cost.it.type'].search([]):
			sql2 += "+"
			sql3 += "+"
			sql2 += """ coalesce("%s",0) """%(elem.code)
			sql3 += """ coalesce("%s",0) """%(elem.code)
			sql += ", \n"
			sql1 += """ coalesce("%s",0) as "%s", """%(elem.code, elem.name)
			sqlsum += """ sum(coalesce("%s",0)) as "%s", """%(elem.code, elem.name)
			sql += """ a.factor*(select sum(debit) from landed_cost_invoice_line where landed_id=%d and type_landed_cost_id = %d) as "%s" """%(self.id,elem.id,elem.code)

		self.env.cr.execute("""(select almacen,codigo,producto,cantidad,factor,valor_p, valormn as "Advalorem ", 
		%s
								%s as total_gv,
								%s as costo_total,
								(%s)/valor_p as factor_d,
								(%s)/cantidad as costo_unitario

								from 
								(
								select   
								b.almacen, 
								b.default_code as codigo, 
								b.name_template as producto, 
								b.ingreso as cantidad,
								a.factor,
								b.debit as valor_p,
								coalesce(c.valormn,0) as valormn %s
								from landed_cost_it_line a
								LEFT JOIN 
								(select almacen, stock_moveid, product_id, default_code, name_template, sum(coalesce(ingreso,0)) as ingreso, sum(coalesce(debit,0)) as debit from get_kardex_v(%s,%s,(select array_agg(id) 
								from product_product),(select array_agg(id) from stock_location),%d) Where ingreso <> 0
								group by almacen, stock_moveid, product_id, default_code, name_template
								having sum(coalesce(ingreso,0)) <> 0
								) b ON b.stock_moveid = a.stock_move_id
								LEFT JOIN stock_move SM on SM.id = b.stock_moveid
								LEFT JOIN (select landed_id, picking_id , product_id, sum(coalesce(valormn,0)) as valormn from landed_cost_advalorem_line GROUP BY landed_id, picking_id, product_id) c ON c.product_id = b.product_id AND a.gastos_id = c.landed_id and SM.picking_id = c.picking_id
								where a.gastos_id = %d
								)tt)
								UNION ALL
								(select '' as almacen,'' as codigo,'' as producto,null as cantidad, null as factor,sum(tt2.valor_p) as valor_p, sum(tt2.valormn) as "Advalorem ", 
		%s
								sum(%s) as total_gv,
								sum(%s) as costo_total,
								null as factor_d,
								null as costo_unitario

								from 
								(
								select   
								b.almacen, 
								b.default_code as codigo, 
								b.name_template as producto, 
								b.ingreso as cantidad,
								a.factor,
								b.debit as valor_p,
								coalesce(c.valormn,0) as valormn %s
								from landed_cost_it_line a
								LEFT JOIN 
								(select almacen, stock_moveid, product_id, default_code, name_template, sum(coalesce(ingreso,0)) as ingreso, sum(coalesce(debit,0)) as debit from get_kardex_v(%s,%s,(select array_agg(id) 
								from product_product),(select array_agg(id) from stock_location),%d) Where ingreso <> 0
								group by almacen, stock_moveid, product_id, default_code, name_template
								having sum(coalesce(ingreso,0)) <> 0
								) b ON b.stock_moveid = a.stock_move_id
								LEFT JOIN stock_move SM on SM.id = b.stock_moveid
								LEFT JOIN (select landed_id , picking_id, product_id, sum(coalesce(valormn,0)) as valormn from landed_cost_advalorem_line GROUP BY landed_id, picking_id, product_id) c ON c.product_id = b.product_id AND a.gastos_id = c.landed_id and SM.picking_id = c.picking_id
								where a.gastos_id = %d
								)tt2)"""%(sql1,
									sql3,
									sql2,
									sql2,
									sql2,
									sql,
									str(today.year)+'0101',
									str(today).replace('-',''),
									self.company_id.id,
									self.id,
									sqlsum,
									sql3,
									sql2,
									sql,
									str(today.year)+'0101',
									str(today).replace('-',''),
									self.company_id.id,
									self.id
								))
		res = self.env.cr.fetchall()
		colnames = [
			desc[0] for desc in self.env.cr.description
		]
		res.insert(0, colnames)

		wb = openpyxl.Workbook()
		ws = wb.active
		row_position = 1
		col_position = 1
		for index, row in enumerate(res, row_position):
			for col, val in enumerate(row, col_position):
				ws.cell(row=index, column=col).value = val
		output = BytesIO()
		wb.save(output)
		output.getvalue()
		output_datas = base64.b64encode(output.getvalue())
		output.close()

		return self.env['popup.it'].get_file('%s.xlsx'%(self.name),output_datas)

class LandedCostInvoiceLine(models.Model):
	_inherit = 'landed.cost.invoice.line'

	type_landed_cost_id = fields.Many2one('landed.cost.it.type',string='Tipo G.V.')
	type_landed_cost = fields.Selection([('advalorem','Advalorem'),
										('flete','Flete'),
										('seguro','Seguro'),
										('adm_contenedor',u'box fee, doc fee,ctrl adm de contenedor'),
										('gasto_adm',u'Gastos administrativos'),
										('carga_dscrg',u'CARGA DSCRGA- CONTENEDORES,ALMACENAJE/GTOS ADM'),
										('traccion',u'TRACCION-CONTENEDORES 40 SECO FULL FCL'),
										('isps','ISPS  / THC - LIQ COBRANZA'),
										('serv_recep','SERVICIO DE RECEPCIÓN DE CONTENEDORES MTY - GATE'),
										('aduana','AG ADUANA/GTOS OPERATIVOS/CUSTODIA/ENTRGA CARGA')],string='Tipo GV')

class LandedCostAdvaloremLine(models.Model):
	_name = 'landed.cost.advalorem.line'
	_description = 'Landed Cost Advalorem Line'

	@api.depends('product_id','landed_id','landed_id.detalle_ids')
	def _check_products(self):
		for object in self:
			object.correct_product = False
			product_list = []
			if object.landed_id:
				for x in object.landed_id.detalle_ids:
					if x.stock_move_id.product_id:
						product_list.append(x.stock_move_id.product_id.id)
			if object.product_id.id in product_list:
				object.correct_product = True
			  
	landed_id = fields.Many2one('landed.cost.it', 'Gastos Vinculado')
	invoice_id = fields.Many2one('account.move.line',string='Factura')
	picking_id = fields.Many2one('stock.picking',string='Referencia')
	product_id = fields.Many2one('product.product',string='Producto')
	valormn = fields.Float(string='Valor MN',digits=(12,2))
	valorme = fields.Float(string='Valor ME',digits=(12,2))
	correct_product = fields.Boolean(string='Producto Pertenece a GV',store=True,compute='_check_products')