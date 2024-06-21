# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	cost_structure_ids = fields.One2many('cost.structure.it', 'sale_order_id', string='Estructura de Costos')
	cost_structure_visible = fields.Boolean(compute='_compute_cost_structure_visible',default=False)

	def _compute_cost_structure_visible(self):
		for sale_order in self:
			if sale_order.cost_structure_ids:
				sale_order.cost_structure_visible = False
			else:
				sale_order.cost_structure_visible = True

	def button_create_cost_structure(self):
		self.ensure_one()

		cost_structure = self.env['cost.structure.it'].create({
			'sale_order_id': self.id,
			'partner_id': self.partner_id.id,
			'date':fields.Date.context_today(self),
			'remuneration_line_ids':[
				(0,0,{
					'name': u'MANO DE OBRA 8 HORAS TURNO MAÑANA',
				}),
				(0,0,{
					'name': 'SUPERVISOR',
				}),
				(0,0,{
					'name': 'SUPERVISOR HORAS EXTRAS',
				}),
				(0,0,{
					'name': u'ASIGNACIÓN FAMILIAR',
				})
			],
			'social_benefit_line_ids':[
				(0,0,{
					'name': 'VACACIONES',
				}),
				(0,0,{
					'name': u'COMPENSACIÓN POR TIEMPO DE SERVICIOS (C.T.S.)',
				}),
				(0,0,{
					'name': 'GRATIFICACIONES',
				}),
				(0,0,{
					'name': 'SEGURO COMPLEMENTARIO DE TRABAJO RIESGO (S.C.T.R.)',
				}),
				(0,0,{
					'name': 'ESSALUD',
				})
			],
			'logistic_line_ids':[
				(0,0,{
					'name': 'MATERIALES + INSUMOS DE SS.HH.',
				}),
				(0,0,{
					'name': 'MAQUINARIA',
				}),
				(0,0,{
					'name': u'DESINSECTACIÓN DE AMBIENTES - TRIMESTRAL',
				}),
				(0,0,{
					'name': u'DESINFECCIÓN DE AMBIENTES - TRIMESTRAL',
				}),
				(0,0,{
					'name': u'FUMIGACIÓN Y DESRATIZACIÓN - TRIMESTRAL',
				}),
				(0,0,{
					'name': u'LIMPIEZA Y DESINFECCIÓN DE TANQUES Y RESERVORIOS DE AGUA - SEMESTRAL',
				}),
				(0,0,{
					'name': 'POLIZAS Y SEGUROS',
				}),
				(0,0,{
					'name': 'UNIFORMES',
				}),
				(0,0,{
					'name': 'EPP',
				})
			],
			'other_line_ids':[
				(0,0,{
					'name': u'EXAMEN MÉDICO',
				})
			],
			'company_id':self.company_id.id,
		})
		action = self.env.ref('cost_structure_it.action_cost_structure_it').read()[0]
		return dict(action, view_mode='form', res_id=cost_structure.id, views=[(False, 'form')])

	def action_view_cost_structure(self):
		self.ensure_one()
		action = self.env.ref('cost_structure_it.action_cost_structure_it').read()[0]
		domain = [('id', 'in', self.cost_structure_ids.ids)]
		context = dict(self.env.context, default_sale_order_id=self.id)
		views = [(self.env.ref('cost_structure_it.view_cost_structure_it_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)