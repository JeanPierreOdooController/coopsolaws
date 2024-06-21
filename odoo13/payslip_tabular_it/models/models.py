from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError

class report_tree_add(models.Model):
    _inherit='hr.payslip.line'

    lote_name = fields.Char(string='Planilla', related='slip_id.payslip_run_id.name', store=True)
