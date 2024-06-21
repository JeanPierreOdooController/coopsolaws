from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    google_analytics_4_key = fields.Char('Google Analytics 4 ID')
    ga4_debug_mode = fields.Boolean(string='Debug Mode')

    def _ga4_params(self, request=None):
        self.ensure_one()
        params = {}
        if self.ga4_debug_mode:
            params.update({'debug_mode': True})
        return params
