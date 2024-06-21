# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    uit = fields.Float(string='Valor de UIT')