# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	retention_type = fields.Selection([('fixed','Importe Fijo'),('percentage','Porcentaje')],default='percentage',string='Tipo de Retencion')
	tasa = fields.Float(string='Tasa')
	amount = fields.Float(string="Monto")

	is_vida_ley = fields.Boolean(string='Tiene + Vida Ley', default=False)
	is_senati = fields.Boolean(string='Tiene Senati', default=False)

	movilidad = fields.Monetary('Movilidad', tracking=True)
	refrigerio = fields.Monetary('Refrigerio', tracking=True)
	bono_cump = fields.Monetary('Bono Cumplimiento', tracking=True)
	bono_proy = fields.Monetary('Bono Proyecto', tracking=True)
	bono_prod = fields.Monetary('Bono Productividad', tracking=True)