# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo import models, api
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
_logger = logging.getLogger(__name__)



class AuthSignupHomeInherit(AuthSignupHome):

	@http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
	def web_auth_signup(self, *args, **kw):
		qcontext = self.get_auth_signup_qcontext()

		if not qcontext.get('token') and not qcontext.get('signup_enabled'):
			raise werkzeug.exceptions.NotFound()

		if 'error' not in qcontext and request.httprequest.method == 'POST':

			try:
				self.do_signup(qcontext)
				# Send an account creation confirmation email
				if qcontext.get('token'):
					user_sudo = request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))])
					template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
					if user_sudo and template:
						template.sudo().with_context(
							lang=user_sudo.lang,
							auth_login=werkzeug.url_encode({'auth_login': user_sudo.email}),
						).send_mail(user_sudo.id, force_send=True)

				user_sudo = request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))])
				#request.env.ref('account.group_show_line_subtotals_tax_excluded').sudo().write({'users':[(3,user_sudo.id)]})
				request.env.cr.execute("""
                                        delete from res_groups_users_rel where gid = """ + str(request.env.ref('account.group_show_line_subtotals_tax_excluded').id)+ """
                                        and uid = """ + str(user_sudo.id) +"""
                                 """)

				#request.env.cr.execute("""
                #                        update res_users set company_id = 9 where id = """ + str(user_sudo.id) +"""
                #                 """)
				#request.env.cr.execute("""
                #                        update res_company_users_rel set cid = 9 where user_id = """ + str(user_sudo.id) +"""
                #                 """)

				#user_sudo.partner_id.sudo().write( { 'property_payment_term_id': request.env['account.payment.term'].sudo().search([('is_credit_control','=',False)])[0].id})
				return self.web_login(*args, **kw)
			except UserError as e:
				qcontext['error'] = e.name or e.value
			except (SignupError, AssertionError) as e:
				qcontext['error'] = str(e)
				#if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
				#    qcontext["error"] = _("Another user is already registered using this email address.")
				#else:
				#    _logger.error("%s", e)
				#    qcontext['error'] = _("Could not create a new account.")


		response = request.render('auth_signup.signup', qcontext)
		response.headers['X-Frame-Options'] = 'DENY'
		return response



class deliverycarrier(models.Model):
	_inherit = 'delivery.carrier'

	almacen_venta = fields.Many2one('stock.warehouse','Almacen')

class res_partner(models.Model):
	_inherit = 'res.partner'

	type_document_id = fields.Many2one('einvoice.catalog.01','Tipo de Facturación')

	@api.model
	def _commercial_fields(self):
		t = super()._commercial_fields()
		if 'website_id' in self.env.context:
			res = []
			for i in t:
				if i != 'vat' and i != 'l10n_latam_identification_type_id':
					res.append(i)
			return res
		else:
			return t


class sale_order(models.Model):
	_inherit = 'sale.order'

	@api.model
	def create(self,vals):
		t = super(sale_order,self).create(vals)
		t.write({})
		return t

	def write(self,vals):
		if self.state == 'draft' and self.website_id.id:
			for lineas in self.order_line:
				deliver = self.env['delivery.carrier'].search([('product_id','=',lineas.product_id.id)])
				if len(deliver)>0:
					vals['warehouse_id'] = deliver[0].almacen_venta.id
		t = super(sale_order,self).write(vals)
		return t

class WebsiteSaleInherit(WebsiteSale):

	def checkout_values(self, **kw):
		order = request.website.sale_get_order(force_create=1)
		shippings = []
		factures = []
		if order.partner_id != request.website.user_id.sudo().partner_id:
			Partner = order.partner_id.with_context(show_address=1).sudo()
			shippings = Partner.search([
				("id", "child_of", order.partner_id.commercial_partner_id.ids),
				'|', ("type", "in", ["delivery", "other"]), ("id", "=", order.partner_id.commercial_partner_id.id)
			], order='id desc')

			factures = Partner.search([
				("id", "child_of", order.partner_id.commercial_partner_id.ids),
				'|', ("type", "in", ["invoice", "other"]), ("id", "=", order.partner_id.commercial_partner_id.id)
			], order='id desc')
			if shippings:
				if kw.get('partner_id') or 'use_billing' in kw:
					if 'use_billing' in kw:
						partner_id = order.partner_id.id
					else:
						partner_id = int(kw.get('partner_id'))
					if partner_id in shippings.mapped('id'):
						order.partner_shipping_id = partner_id
				elif not order.partner_shipping_id:
					last_order = request.env['sale.order'].sudo().search([("partner_id", "=", order.partner_id.id)], order='id desc', limit=1)
					order.partner_shipping_id.id = last_order and last_order.partner_shipping_id and last_order.partner_shipping_id.id

			if factures:
				if kw.get('partner_id') or 'use_billing' in kw:
					if 'use_billing' in kw:
						partner_id = order.partner_id.id
					else:
						partner_id = int(kw.get('partner_id'))
					if partner_id in factures.mapped('id'):
						order.partner_invoice_id = partner_id
				elif not order.partner_invoice_id:
					last_order = request.env['sale.order'].sudo().search([("partner_id", "=", order.partner_id.id)], order='id desc', limit=1)
					order.partner_invoice_id.id = last_order and last_order.partner_invoice_id and last_order.partner_invoice_id.id

		values = {
			'order': order,
			'shippings': shippings,
			'factures': factures,
			'only_services': order and order.only_services or False
		}
		return values


	@http.route(['/shop/country_infos/<model("res.country"):country>'], type='json', auth="public", methods=['POST'], website=True)
	def country_infos(self, country, mode, **kw):
		return dict(
			fields=country.get_address_fields(),
			states=[(st.id, st.state_id.name + '-'+ st.province_id.name + '-' + st.name + ' (' + st.code + ')', st.code) for st in country.get_website_sale_states(mode=mode).filtered(lambda stateX: stateX.state_id.id and stateX.province_id.id )  ],
			phone_code=country.phone_code
		)

	def values_postprocess(self, order, mode, values, errors, error_msg):
		new_values = {}
		authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()

		for k, v in values.items():
			# don't drop empty value, it could be a field to reset
			if k in authorized_fields and v is not None:
				new_values[k] = v
			else:  # DEBUG ONLY
				if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
					_logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)

		new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
		new_values['user_id'] = request.website.salesperson_id and request.website.salesperson_id.id

		if request.website.specific_user_account:
			new_values['website_id'] = request.website.id

		if mode[0] == 'new':
			new_values['company_id'] = request.website.company_id.id

		lang = request.lang.code if request.lang.code in request.website.mapped('language_ids.code') else None
		if lang:
			new_values['lang'] = lang
		if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
			new_values['type'] = 'other'
		if mode[1] == 'shipping':
			new_values['parent_id'] = order.partner_id.commercial_partner_id.id
			new_values['type'] = 'delivery'
		if mode[1] == 'facturacion':
			new_values['parent_id'] = order.partner_id.commercial_partner_id.id
			new_values['type'] = 'invoice'

		new_values['l10n_latam_identification_type_id'] = values['l10n_latam_identification_type_id']
		new_values['type_document_id'] = values.get('type_document_id',False)

		return new_values, errors, error_msg


	def values_preprocess(self, order, mode, values):
		# Convert the values for many2one fields to integer since they are used as IDs
		partner_fields = request.env['res.partner']._fields
		t = {
			k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == 'many2one' else v
			for k, v in values.items()
		}
		return t

	def _checkout_form_save(self, mode, checkout, all_values):
		Partner = request.env['res.partner']
		if mode[0] == 'new':
			partner_exis = Partner.sudo().search([('vat','=',checkout['vat']),('company_id','=',checkout['company_id']),('l10n_latam_identification_type_id','=',checkout['l10n_latam_identification_type_id'])])
			if len(partner_exis)>0:
				Partner.sudo().with_context(tracking_disable=True,nocopiardefault=True).write(checkout)
				partner_id = partner_exis[0].id
			else:
				partner_id = Partner.sudo().with_context(tracking_disable=True,nocopiardefault=True).create(checkout).id
		elif mode[0] == 'edit':
			partner_id = int(all_values.get('partner_id', 0))
			
			if partner_id:
				# double check
				order = request.website.sale_get_order()
				shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])

				
				if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:

					
					return Forbidden()
				Partner.browse(partner_id).sudo().write(checkout)

		
		return partner_id


	def _get_mandatory_billing_fields(self):
		return ["name", "email", "street", "city", "country_id","l10n_latam_identification_type_id","vat","zip", "type_document_id"]

	def _get_mandatory_shipping_fields(self):
		return ["name", "email", "street", "city", "country_id","l10n_latam_identification_type_id","vat","zip"]

	def _get_mandatory_invoice_fields(self):
		return ["name", "email", "street", "city", "country_id","l10n_latam_identification_type_id","vat","zip", "type_document_id"]

	def checkout_form_validate(self, mode, all_form_values, data):
		# mode: tuple ('new|edit', 'billing|shipping')
		# all_form_values: all values before preprocess
		# data: values after preprocess
		error = dict()
		error_message = []

		# Required fields from form
		required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
		# Required fields from mandatory field function
		if mode[1] == 'shipping':
			required_fields += self._get_mandatory_shipping_fields()
		elif mode[1] == 'facturacion':
			required_fields += self._get_mandatory_invoice_fields()
		else:
			required_fields += self._get_mandatory_billing_fields()
		# Check if state required
		country = request.env['res.country']
		if data.get('country_id'):
			country = country.browse(int(data.get('country_id')))
			if 'state_code' in country.get_address_fields() and country.state_ids:
				required_fields += ['state_id']

		# error message for empty required fields
		for field_name in required_fields:
			if not data.get(field_name):
				error[field_name] = 'missing'

		# email validation
		if data.get('email') and not tools.single_email_re.match(data.get('email')):
			error["email"] = 'error'
			error_message.append(_('Invalid Email! Please enter a valid email address.'))

		# vat validation
		"""Partner = request.env['res.partner']
		if data.get("vat") and hasattr(Partner, "check_vat"):
			if data.get("country_id"):
				data["vat"] = Partner.fix_eu_vat_number(data.get("country_id"), data.get("vat"))
			partner_dummy = Partner.new({
				'vat': data['vat'],
				'country_id': (int(data['country_id'])
							   if data.get('country_id') else False),
			})
			try:
				partner_dummy.check_vat()
			except ValidationError:
				error["vat"] = 'error'"""

		if [err for err in error.values() if err == 'missing']:
			error_message.append(_('Some required fields are empty.'))

		return error, error_message


	@http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
	def address(self, **kw):
		Partner = request.env['res.partner'].with_context(show_address=1).sudo()
		order = request.website.sale_get_order()

		redirection = self.checkout_redirection(order)
		if redirection:
			return redirection

		mode = (False, False)
		can_edit_vat = False
		def_country_id = order.partner_id.country_id
		values, errors = {}, {}

		partner_id = int(kw.get('partner_id', -1))

		# IF PUBLIC ORDER
		if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
			mode = ('new', 'billing')
			can_edit_vat = True
			country_code = request.session['geoip'].get('country_code')
			if country_code:
				def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
			else:
				def_country_id = request.website.user_id.sudo().country_id
		# IF ORDER LINKED TO A PARTNER
		else:
			if partner_id > 0:
				if kw.get('facturacion', False) and partner_id:
					mode = ('edit','facturacion')
				elif partner_id == order.partner_id.id:
					mode = ('edit', 'billing')
					can_edit_vat = order.partner_id.can_edit_vat()
				else:
					shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
					if partner_id in shippings.mapped('id'):
						mode = ('edit', 'shipping')
					else:
						return Forbidden()
				if mode:
					values = Partner.browse(partner_id)
			elif partner_id == -1:

				if kw.get('facturacion', False):
					mode = ('new','facturacion')
				else:
					mode = ('new', 'shipping')
			else: # no mode - refresh without post?
				return request.redirect('/shop/checkout')

		# IF POSTED
		if 'submitted' in kw:
			pre_values = self.values_preprocess(order, mode, kw)
			
			errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)

			
			post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

			if errors:
				errors['error_message'] = error_msg
				values = kw
			else:
				partner_id = self._checkout_form_save(mode, post, kw)
				if mode[1] == 'billing':
					order.partner_id = partner_id
					order.onchange_partner_id()
					# This is the *only* thing that the front end user will see/edit anyway when choosing billing address
					if not kw.get('use_same'):
						kw['callback'] = kw.get('callback') or \
							(not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
				elif mode[1] == 'shipping':
					order.partner_shipping_id = partner_id
				elif mode[1] == 'facturacion':
					order.partner_invoice_id = partner_id

				order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
				if not errors:
					return request.redirect(kw.get('callback') or '/shop/confirm_order')

		country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
		country = country and country.exists() or def_country_id
		
		l10n_latam_identification_type_id = request.env['l10n_latam.identification.type'].search([('name','in',('VAT','DNI'))])
		type_document_id = request.env['einvoice.catalog.01'].search([('code','in',('01','03'))])

		render_values = {
			'website_sale_order': order,
			'partner_id': partner_id,
			'mode': mode,
			'checkout': values,
			'can_edit_vat': can_edit_vat,
			'country': country,
			'countries': country.get_website_sale_countries(mode=mode[1]),
			"states": country.get_website_sale_states(mode=mode[1]),
			'error': errors,
			'callback': kw.get('callback'),
			'only_services': order and order.only_services,
			'l10n_latam_identification_type_ids': l10n_latam_identification_type_id,
			'type_document_ids' : type_document_id,
		}
		return request.render("website_sale.address", render_values)