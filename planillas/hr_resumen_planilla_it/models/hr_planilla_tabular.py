# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrPlanillaTabularResumen(models.Model):
	_name = 'hr.planilla.tabular.resumen'
	_description = 'Hr Planilla Tabular Resumen'
	_auto = False

	employee_id = fields.Many2one('hr.employee','Empleado')
	# contract_id = fields.Many2one('hr.contract','Contrato')
	identification_id = fields.Char('N° Identificacion')
	salary_rule_id = fields.Many2one('hr.salary.rule', string='Concepto Remunerativo')
	sequence = fields.Integer(string='Secuencia')
	code = fields.Char(string='Codigo')
	amount = fields.Float('Importe')
