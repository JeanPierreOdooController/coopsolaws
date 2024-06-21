# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ConsolidationAccount(models.Model):
	_inherit = "consolidation.account"

	currency_mode = fields.Selection(selection_add=[('end_purchase', 'Tasa Cierre Compra'),('avg_purchase', 'Tasa Promedio Compra')])

class ConsolidationCompanyPeriod(models.Model):
	_inherit = "consolidation.company_period"

	currency_rate_avg_purchase = fields.Float(string="Pro Compras", default=1.0, digits=[12,12])
	currency_rate_end_purchase = fields.Float(string="Cierre Compras", default=1.0, digits=[12,12])