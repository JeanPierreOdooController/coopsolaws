# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrPayrollStructure(models.Model):
	_inherit = 'hr.payroll.structure'

	type_id = fields.Many2one('hr.payroll.structure.type', required=False)
	struct_type_ids = fields.Many2many('hr.payroll.structure.type', 'payroll_structure_type_rel', 'structure_id', 'type_id', string="Tipos de Estructuras")