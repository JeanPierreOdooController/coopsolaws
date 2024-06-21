# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class kardex_cerrado_config(models.Model):
	_name = 'kardex.cerrado.config'

	name = fields.Char('Nombre',required=True)
	fecha_inicio = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)
	listado_locaciones = fields.Many2many('stock.location','kardex_cerrador_locaciones_rel','kardex_cc_id','location_id','Ubicaciones')
	company_id = fields.Many2one('res.company','Compania',required=True, default=lambda self: self.env.company,readonly=True)

class gastos_vinculados_it(models.Model):
	_inherit = 'landed.cost.it'


	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
			
		t = super(gastos_vinculados_it,self).create(vals)

		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date_kardex)[:10] >= str(i.fecha_inicio) and str(t.date_kardex)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación, detalle:" + str(vals) )
			return t

		return t

	
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		t = super(gastos_vinculados_it,self).copy(default)

		if True:			
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date_kardex)[:10] >= str(i.fecha_inicio) and str(t.date_kardex)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t


	
	def write(self,vals):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		t = super(gastos_vinculados_it,self).write(vals)
		self.refresh()

		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date_kardex)[:10] >= str(i.fecha_inicio) and str(self.date_kardex)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación, detalle:2" + str(vals))
			return t

		return t

	
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date_kardex)[:10] >= str(i.fecha_inicio) and str(self.date_kardex)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(gastos_vinculados_it,self).unlink()
		return super(gastos_vinculados_it,self).unlink()





class account_invoice(models.Model):
	_inherit = 'account.move'



	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
			
		t = super(account_invoice,self).create(vals)

		flag = False
		for linea in t.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].analytic_tag_kardex.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].analytic_tag_kardex.id:
					flag = True

		if flag:			
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date)[:10] >= str(i.fecha_inicio) and str(t.date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t

	
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		t = super(account_invoice,self).copy(default)

		flag = False
		for linea in t.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].analytic_tag_kardex.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].analytic_tag_kardex.id:
					flag = True

		if flag:			
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date)[:10] >= str(i.fecha_inicio) and str(t.date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t


	
	def write(self,vals):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		t = super(account_invoice,self).write(vals)
		self.refresh()
		flag = False

		for linea in self.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].analytic_tag_kardex.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].analytic_tag_kardex.id:
					flag = True
		
		
		if flag:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date)[:10] >= str(i.fecha_inicio) and str(self.date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
		return t

	
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		flag = False

		for linea in self.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].analytic_tag_kardex.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].analytic_tag_kardex.id:
					flag = True
		
		if flag:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date)[:10] >= str(i.fecha_inicio) and str(self.date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(account_invoice,self).unlink()
		return super(account_invoice,self).unlink()






class stock_picking(models.Model):
	_inherit = 'stock.picking'

	
	def nohacernada(self):
		return

	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
				
		if True:
			t = super(stock_picking,self).create(vals)
			if len(vals.keys() )== 1:
				if 'invoice_id' in vals:
					return t
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.kardex_date)[:10] >= str(i.fecha_inicio) and str(t.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación, detalle:3" + str(vals))
			return t

		return super(stock_picking,self).create(vals)

	
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		if True:
			t = super(stock_picking,self).copy(default)
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.kardex_date)[:10] >= str(i.fecha_inicio) and str(t.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return super(stock_picking,self).copy(default)

	
	def write(self,vals):
		m = super(stock_picking,self).write(vals)

		if len(vals.keys() )== 1:
			if 'invoice_id' in vals:
				return m

		self.refresh()

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']		
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.kardex_date)[:10] >= str(i.fecha_inicio) and str(self.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación, detalle:4" + str(vals))
			return m

		return m

	
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.kardex_date)[:10] >= str(i.fecha_inicio) and str(self.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(stock_picking,self).unlink()
		return super(stock_picking,self).unlink()




class stock_move(models.Model):
	_inherit = 'stock.move'


	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			t = super(stock_move,self).create(vals)
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.picking_id.kardex_date)[:10] >= str(i.fecha_inicio) and str(t.picking_id.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación, detalle:6" + str(vals))
			return t

		return super(stock_move,self).create(vals)

	
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			t = super(stock_move,self).copy(default)
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.picking_id.kardex_date)[:10] >= str(i.fecha_inicio) and str(t.picking_id.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

	
	def write(self,vals):
		m = super(stock_move,self).write(vals)

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.picking_id.kardex_date)[:10] >= str(i.fecha_inicio) and str(self.picking_id.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación, detalle:7" + str(vals))
			return m

		return m

	
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.picking_id.kardex_date)[:10] >= str(i.fecha_inicio) and str(self.picking_id.kardex_date)[:10] <= str(i.fecha_fin):
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(stock_move,self).unlink()
		return super(stock_move,self).unlink()
