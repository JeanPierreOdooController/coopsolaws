from odoo.addons.portal.controllers.portal import CustomerPortal

import base64
import json
import math
import re

from werkzeug import urls

from odoo import fields as odoo_fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq


class CustomerPortal(CustomerPortal):
    #MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name",'province_id','district_id','l10n_latam_identification_type_id']

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(['country_id', 'state_id','province_id','district_id','l10n_latam_identification_type_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({'zip': values.pop('zipcode', '')})

                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        #aqui agregue el codigo
        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(
            int(values['country_id']))
        country = country and country.exists() or partner.country_id or countries[0]

        state = 'state_id' in values and values['state_id'] != '' and request.env['res.country.state'].browse(
            int(values['state_id']))
        state = (state and state.exists()) or partner.state_id or states[0]

        province = 'province_id' in values and values['province_id'] != '' and request.env['res.country.state'].browse(
            int(values['province_id']))

        province = province or partner.province_id or request.env['res.country.state'].sudo().search([],limit=1)

        district = 'district_id' in values and values['district_id'] != '' and request.env['res.country.state'].browse(
            int(values['district_id']))

        district = district or partner.district_id or request.env['res.country.state'].search([],limit=1)

        mode = ('edit', 'billing')

        diwstricts = province.get_website_sale_district(mode=mode[1])

        document = 'l10n_latam_identification_type_id' in values and values[
            'l10n_latam_identification_type_id'] != '' and request.env['l10n_latam.identification.type'].browse(
            int(values['l10n_latam_identification_type_id']))
        document = document  or partner.l10n_latam_identification_type_id  or request.env['l10n_latam.identification.type'].sudo().search([],limit=1)

        documents = request.env['l10n_latam.identification.type'].search([])

        zip = 'zip' in values and values['zip'] != ''
        zip = zip or None


        values.update({
            'partner': partner,
            #'countries': countries,
            #'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',

            'country': country,
            'state': state,
            'province': province,
            'district': district,
            'countries': country.get_website_sale_countries(mode=mode[1]),
            'provinces': province.get_website_sale_provinces(mode=mode[1]),
            'districts': diwstricts,
            "states": country.get_website_sale_states(mode=mode[1]),
            'zip': zip,
            'document': document,
            'documents': documents
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation


        for field_name in self.MANDATORY_BILLING_FIELDS:
            if field_name == 'city':
                continue
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        partner = request.env.user.partner_id
        if data.get("vat") and partner and partner.vat != data.get("vat"):
            if partner.can_edit_vat():
                if hasattr(partner, "check_vat"):
                    if data.get("country_id"):
                        data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")),
                                                                                   data.get("vat"))
                    partner_dummy = partner.new({
                        'vat': data['vat'],
                        'country_id': (int(data['country_id'])
                                       if data.get('country_id') else False),
                    })
                    try:
                        partner_dummy.check_vat()
                    except ValidationError:
                        error["vat"] = 'error'
            else:
                error_message.append(
                    _('Changing VAT number is not allowed once document(s) have been issued for your account. Please contact us directly for this operation.'))

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        fields_avaialable  = self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS

        unknown = [k for k in data if k not in fields_avaialable ]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message
