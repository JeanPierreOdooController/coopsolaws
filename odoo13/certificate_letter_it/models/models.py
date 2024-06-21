# from typing_extensions import Required
from odoo import models, fields, api
from datetime import datetime
from datetime import date
from openerp.exceptions import ValidationError

# from odoo.osv import expression
# from odoo.tools import float_is_zero, float_compare


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def open_wizard_certificate(self):
        return {
            'name': 'Certificado de Trabajo PDF',
            'res_model': 'hr.certificate.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_employee_id': self.id},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def open_wizard_letter(self):
        return {
            'name': 'Carta Retiro PDF',
            'res_model': 'hr.letter.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_employee_id': self.id},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class certificate(models.TransientModel):
    _name = 'hr.certificate.wizard'

    employee_id = fields.Many2one('hr.employee', string='Empleado a Certificar')
    des_empl = fields.Selection([
        ('el Sr.', 'Señor'),
        ('la Sra.', 'Señora'),
        ('la Srta.', 'Señorita')
    ], string='Tratamiento')
    # employee_firma = fields.Many2one('hr.employee', string='Empleado que Firma')
    date_ini = fields.Date(string='Fecha Inicial')
    date_fin = fields.Date(string='Fecha Final')
    city = fields.Char(string='Ciudad')

    company_current = fields.Many2one('res.company', string='')

    day = fields.Integer(string='Dia')
    month = fields.Char(string='Mes')
    year = fields.Integer(string='Año')

    def export_certificate(self):
        current_date = date.today()
        ar = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']
        self.day = current_date.day
        self.month = ar[current_date.month - 1]
        self.year = current_date.year

        self.company_current = self.env['res.company'].search( [('id', '=', self.env.context['allowed_company_ids'])] )

        if self.employee_id.id == False:
            raise ValidationError('Ingrese Empleado')
        if self.des_empl == False:
            raise ValidationError('Ingrese Descripción de Empleado a Certificar')
        # if self.employee_firma.id == False:
        #     raise ValidationError('Ingrese Empleado que Firmará')
        if self.city == False:
            raise ValidationError('Ingrese Ciudad')
        if self.date_ini == False:
            raise ValidationError('Ingrese Fecha Inicial')
        if self.date_fin == False:
            raise ValidationError('Ingrese Fecha Final')
        return self.env.ref('certificate_letter_it.action_report_certificate').report_action(self)


class letter(models.TransientModel):
    _name = 'hr.letter.wizard'

    employee_id = fields.Many2one('hr.employee', string='Empleado')
    des_empl = fields.Selection([
        ('el Sr.', 'Señor'),
        ('la Sra.', 'Señora'),
        ('la Srta.', 'Señorita')
    ], string='Tratamiento')
    # employee_firma = fields.Many2one('hr.employee', string='Empleado que Firma')
    # bank = fields.Many2one('res.bank', string='Banco')
    date_fin = fields.Date(string='Fecha Final')
    city = fields.Char(string='Compañia Ciudad')

    company_current = fields.Many2one('res.company', string='')

    day_now = fields.Integer(string='Dia')
    month_now = fields.Char(string='Mes')
    year_now = fields.Integer(string='Año')

    day_fin = fields.Integer(string='Dia')
    month_fin = fields.Char(string='Mes')
    year_fin = fields.Integer(string='Año')

    def export_letter(self):
        current_date = date.today()
        ar = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']
        self.day_now = current_date.day
        self.month_now = ar[current_date.month - 1]
        self.year_now = current_date.year

        self.day_fin = self.date_fin.day
        self.month_fin = ar[self.date_fin.month - 1]
        self.year_fin = self.date_fin.year

        self.company_current = self.env['res.company'].search( [('id', '=', self.env.context['allowed_company_ids'])] )

        if self.employee_id.id == False:
            raise ValidationError('Ingrese Empleado')
        if self.des_empl == False:
            raise ValidationError('Ingrese Descripción de Empleado a Certificar')
        # if self.employee_id.id == False:
        #     raise ValidationError('Ingrese Empleado Firma')
        # if self.bank.id == False:
        #     raise ValidationError('Ingrese Banco')
        if self.city == False:
            raise ValidationError('Ingrese Ciudad')
        if self.date_fin == False:
            raise ValidationError('Ingrese Fecha Final')
        return self.env.ref('certificate_letter_it.action_report_letter').report_action(self)
