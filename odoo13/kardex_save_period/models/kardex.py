# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class KardexSave(models.Model):
	_name = 'kardex.save'

	name = fields.Many2one('account.period',string='Periodo')
	state = fields.Selection([('draft', 'Borrador'), ('done', 'Almacenado')],string='Estado', default='draft')
	date = fields.Datetime('Fecha Guardado')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)


	@api.constrains('name')
	def _verify_period(selfs):
		for self in selfs:
			if len(self.env['kardex.save'].search([('name','=',self.name.id)],limit=2)) > 1:
				raise UserError('No pueden existir dos guardados del mismo periodo')

	def save(self):
		self.state = 'done'
		self.date = str(fields.Datetime.now())
		self.env.cr.execute("""

			create table  kardex_save_""" +str( self.name.code.replace('/','_') )+ """_"""+str(self.env.company.id)+"""  as

select T.*,datos.cprom from (
select 
max(almacen) AS "Almacén",
max(categoria) as "Categoria",
producto as "Producto",
cod_pro as "Codigo P.",
max(unidad) as "unidad",
max(vstf.fecha) as "Fecha",
sum(vstf.entrada) as "Entrada",
sum(vstf.salida) as "Salida",
categoria_id,
p_id,
alm_id,
lote
from
(
select location_dest_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id,location_dest_id as almacen_id, lote from vst_kardex_fisico_lote(""" +str(self.env.company.id)+ """) as vst_kardex_fisico
union all
select location_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id, location_id as almacen_id, lote from vst_kardex_fisico_lote(""" +str(self.env.company.id)+ """) as vst_kardex_fisico
) as vstf
where vstf.estado = 'done'
and vstf.fecha::date >='""" +str( self.name.date_end ).split('-')[0]+ """-01-01' and vstf.fecha::date <='""" +str( self.name.date_end )+ """'
group by
producto,cod_pro,categoria_id, p_id, alm_id,lote ) T
left join ( SELECT *
FROM (
SELECT *, row_number() OVER (
PARTITION BY almacen, product_id
ORDER BY almacen, product_id, fecha desc
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
) AS _max 
,
LAST_VALUE(cprom) OVER (
PARTITION BY almacen, product_id
ORDER BY almacen, product_id, fecha desc
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
) AS final_cprom
FROM (select * from get_kardex_v(""" +str( self.name.date_end ).split('-')[0]+ """0101,""" +str( self.name.date_end).replace('-','') + """,(select array_agg(id) from product_product),(select array_agg(id) from stock_location),""" +str(self.env.company.id)+ """)t)x
) AS sub
where _max = 1 ) datos on datos.location_id = T.alm_id and datos.product_id = T.p_id;

			""")

	def draft(self):
		self.state = 'draft'
		self.env.cr.execute("""

			drop table  kardex_save_""" +str( self.name.code.replace('/','_') )+ """_"""+str(self.env.company.id)+"""
			""")
