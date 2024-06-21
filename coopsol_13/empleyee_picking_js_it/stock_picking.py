from odoo import fields, models , api , _

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    hr_employee_id = fields.Many2one('hr.employee',string="Empleado")