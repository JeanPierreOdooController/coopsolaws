from odoo import models, api, fields, exceptions


class WebsiteRewrite(models.Model):
	_inherit = 'website.page'

	custom_field = fields.Boolean(string='Filtrar')
	#@api.multi
	def unlink(self):
		for record in self:
			if record.custom_field:
				raise exceptions.ValidationError("No puede eliminar la pagina de '404 no se encontro'")
			# if record.id == 7:
			# 	raise exceptions.ValidationError("No puede eliminar la pagina de '404 no se encontro'")
		return super(WebsiteRewrite, self).unlink()