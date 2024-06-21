from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound
import logging

_logger = logging.getLogger(__name__)
from odoo.addons.website.controllers.main import QueryURL

from odoo.exceptions import UserError
import json
from odoo import fields, http, SUPERUSER_ID, tools
from odoo.exceptions import ValidationError


class WebsiteSale(WebsiteSale):
    def _get_mandatory_billing_fields(self):
        return ["name", "email", "street", "country_id", "state_id", "province_id", "district_id",
                "l10n_latam_identification_type_id"]

    def _get_mandatory_shipping_fields(self):
        return ["name", "street", "country_id", "state_id", "province_id", "district_id"]

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values = {}
        authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()
        # my_fields = ['state_id', 'province_id', 'district_id', 'zip', 'correo_contacto', 'name_contactoit', 'despacho',
        #             "l10n_latam_identification_type_id"]

        my_fields = ['state_id', 'province_id', 'district_id', 'zip', "l10n_latam_identification_type_id"]

        for k, v in values.items():
            # don't drop empty value, it could be a field to reset

            # raise ValueError(k)
            if (k in authorized_fields or k in my_fields) and v is not None:
                new_values[k] = v
            else:  # DEBUG ONLY
                if k not in ('field_required', 'partner_id', 'callback', 'submitted'):  # classic case
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

        return new_values, errors, error_msg

    def checkout_form_validate(self, mode, all_form_values, data):
        # mode: tuple ('new|edit', 'billing|shipping')
        # all_form_values: all values before preprocess
        # data: values after preprocess
        error = dict()
        error_message = []

        # Required fields from form
        required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
        # Required fields from mandatory field function
        required_fields += mode[
                               1] == 'shipping' and self._get_mandatory_shipping_fields() or self._get_mandatory_billing_fields()
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
            error_message.append(('Invalid Email! Please enter a valid email address.'))

        # vat validation
        Partner = request.env['res.partner']
        phone = data.get("phone")
        try:
            #eliminar espacios en blanco
            data["phone"] = phone.replace(" ", "")
            raise ValueError(data.get("phone"))
        except:
            a = 1

        if data.get("vat") and hasattr(Partner, "check_vat"):
            if data.get("country_id"):
                data["vat"] = Partner.fix_eu_vat_number(data.get("country_id"), data.get("vat"))
            partner_dummy = Partner.new({
                'vat': data['vat'],
                'country_id': (int(data['country_id'])
                               if data.get('country_id') else False),
            })
            '''
            try:
                partner_dummy.check_vat()
            except ValidationError:
                error["vat"] = 'error'
            '''

        if [err for err in error.values() if err == 'missing']:
            error_message.append(('Some required fields are empty.'))

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
        def_state_id = order.partner_id.state_id
        def_province_id = order.partner_id.province_id
        def_district_id = order.partner_id.district_id
        def_zip = order.partner_id.zip
        def_document_id = order.partner_id.l10n_latam_identification_type_id
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            return request.redirect('/web/login')
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
                if partner_id == order.partner_id.id:
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
                mode = ('new', 'shipping')
            else:  # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:

            pre_values = self.values_preprocess(order, mode, kw)
            # raise ValueError(pre_values)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                                         (not order.only_services and (
                                                 mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/confirm_order')

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(
            int(values['country_id']))
        country = country and country.exists() or def_country_id

        state = 'state_id' in values and values['state_id'] != '' and request.env['res.country.state'].browse(
            int(values['state_id']))
        state = state and state.exists() or def_state_id

        province = 'province_id' in values and values['province_id'] != '' and request.env['res.country.state'].browse(
            int(values['province_id']))

        province = province or def_province_id

        district = 'district_id' in values and values['district_id'] != '' and request.env['res.country.state'].browse(
            int(values['district_id']))

        district = district or def_district_id

        diwstricts = province.get_website_sale_district_js(mode=mode[1])

        document = 'l10n_latam_identification_type_id' in values and values[
            'l10n_latam_identification_type_id'] != '' and request.env['l10n_latam.identification.type'].browse(
            int(values['l10n_latam_identification_type_id']))
        document = document or def_document_id

        documents = request.env['l10n_latam.identification.type'].search([])

        zip = 'zip' in values and values['zip'] != ''
        zip = zip or def_zip

        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'country': country,
            'state': state,
            'province': province,
            'district': district,
            'countries': country.get_website_sale_countries_js(mode=mode[1]),
            'provinces': province.get_website_sale_provinces_js(mode=mode[1]),
            'districts': diwstricts,
            "states": country.get_website_sale_states_js(mode=mode[1]),
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services,
            'zip': zip,
            'document': document,
            'documents': documents
        }
        return request.render("website_sale.address", render_values)
    '''

    @http.route(['/shop/states_infos/<model("res.country.state"):state>'], type='json',
                auth="public", methods=['POST'],
                website=True)
    def states_infos(self, state, mode=None, **kw):
        country = state.country_id
        provinces = state.get_website_sale_provinces()
        return dict(
            fields=country.get_address_fields(),
            states=[(st.id, st.name, st.code) for st in provinces],
            phone_code=country.phone_code
        )

    @http.route(['/shop/province_infos/<model("res.country.state"):state>'], type='json',
                auth="public", methods=['POST'],
                website=True)
    def province_infos(self, state, mode=None, **kw):
        country = state.country_id
        provinces = state.get_website_sale_district()
        return dict(
            fields=country.get_address_fields(),
            states=[(st.id, st.name, st.code) for st in provinces],
            phone_code=country.phone_code
        )

    @http.route(['/shop/district/<model("res.country.state"):state>'], type='json',
                auth="public", methods=['POST'],
                website=True)
    def district_id(self, state, mode=None, **kw):
        return state.code if state else None

    @http.route(['/shop/verify_doc/<model("l10n_latam.identification.type"):state>'], type='json',
                auth="public", methods=['POST'],
                website=True)
    def verify_doc(self, state, mode=None, **kw):
        vat = kw['vat']
        res = request.env['res.partner'].verify_doc(vat, state)
        return res
    '''

