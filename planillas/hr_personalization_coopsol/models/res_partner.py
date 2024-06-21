# -*- coding:utf-8 -*-
from odoo import api, fields, models

class ResPartner(models.Model):
	_inherit = 'res.partner'

	tasa_vida_emp = fields.Float(string='Tasa Empleado')
	tasa_vida_obr = fields.Float(string='Tasa Obrero')
	tasa_sctr_sal_emp = fields.Float(string='Tasa Empleado')
	tasa_sctr_sal_obr = fields.Float(string='Tasa Obrero')
	tasa_sctr_pen_emp = fields.Float(string='Tasa Empleado')
	tasa_sctr_pen_obr = fields.Float(string='Tasa Obrero')