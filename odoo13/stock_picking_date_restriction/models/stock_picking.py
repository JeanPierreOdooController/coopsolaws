# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

 
    def write(self, vals):
        res = super(StockPicking, self).write(vals)

        
        if 'kardex_date' in vals and vals['kardex_date']:	
            for record in self:		
                new_date = record.kardex_date - timedelta(hours=5)
                current_date = datetime.now() - timedelta(hours=5)

                new_date = new_date.date()  # Obtener solo la fecha de new_date
                current_date = current_date.date()  # Obtener solo la fecha de current_date

                if new_date > current_date:
                    raise UserError('No puedes seleccionar una fecha mayor a hoy para el campo Kardex Date.')
        return res