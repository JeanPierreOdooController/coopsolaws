from odoo import models , fields
from odoo.exceptions import UserError
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    from suds.client import Client
except:
    install('suds-py3')


class ResCountry(models.Model):
    _inherit = 'res.country'
    show_ecommerce = fields.Boolean(default=True,string="Ecommerce")

    def disabled_ecommerce(self):
        for record in self:
            record.show_ecommerce = False

    def active_ecommerce(self):
        for record in self:
            record.show_ecommerce = True

    def get_website_sale_countries_js(self, mode='billing'):
        return self.sudo().search([('show_ecommerce','=',True)])
    def get_website_sale_states_js(self, mode='billing'):
        states = self.sudo().state_ids
        state_ids = []
        for s in states:
            if not s.province_id  and not s.state_id:
                state_ids.append(s)
        return state_ids

class ResCountryStates(models.Model):
    _inherit = 'res.country.state'
    show_ecommerce = fields.Boolean(default=True,string="Ecommerce")
    def get_website_sale_provinces_js(self, mode='billing'):
        provinces = self.env['res.country.state'].search([('state_id','=',self.id),
                                                          ('province_id','=',False),('show_ecommerce','=',True)])
        return provinces
    def get_website_sale_district_js(self, mode='billing'):
        provinces = self.env['res.country.state'].search([('province_id','=',self.id),('show_ecommerce','=',True)])
        return provinces

    def disabled_ecommerce(self):
        for record in self:
            record.show_ecommerce = False

    def active_ecommerce(self):
        for record in self:
            record.show_ecommerce = True


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def verify_doc(self,vat,doctype):
        if doctype == self.env['main.parameter'].sudo().search(
                [('company_id', '=', self.env.company.id)], limit=1).dt_sunat_ruc:
            parameters = self.env['sale.main.parameter'].verify_query_parameters()
            client = Client(parameters.query_ruc_url, faults=False, cachingpolicy=1,
                            location=parameters.query_ruc_url)
            result = client.service.consultaRUC(vat, parameters.query_email, parameters.query_token,
                                                parameters.query_type)

            texto = result[1].split('|')

            flag = False
            for i in texto:
                tmp = i.split('=')
                if tmp[0] == 'status_id' and tmp[1] == '1':
                    flag = True

            if flag:
                name = street = zip = country_id = state_id = province_id = district_id = pais =  None

                # obtner el distrito - provincia - departamento
                departamento_string = provincia_string = distrito_string = dep_pro_dis = None

                for j in texto:
                    tmp = j.split('=')
                    if tmp[0] == 'n1_ubigeo_dep':
                        departamento_string = tmp[1]
                    if tmp[0] == 'n1_ubigeo_pro':
                        provincia_string = tmp[1]
                    if tmp[0] == 'n1_ubigeo_dis':
                        distrito_string = tmp[1]
                if departamento_string and provincia_string and distrito_string:
                    dep_pro_dis = f"{departamento_string} - {provincia_string} - {distrito_string}"





                for j in texto:
                    tmp = j.split('=')
                    if str(tmp[0]) == 'n1_alias':
                        name = tmp[1]
                    if str(tmp[0]) == 'n1_direccion':
                        #street = tmp[1]
                        direccionx = tmp[1]
                        # quitar el pais - distrito - departamento
                        if dep_pro_dis:
                            direccionx = direccionx.replace(dep_pro_dis, '')
                        # raise ValueError(direccionx)
                        street = direccionx



                    if str(tmp[0]) == 'n1_ubigeo':

                        ubi_t = tmp[1]
                        ubigeo = self.env['res.country.state'].search([('code', '=', ubi_t)])

                        if ubigeo:
                            zip = tmp[1]
                            pais = self.env['res.country'].search([('code', '=', 'PE')])
                            ubidepa = ubi_t[0:2]
                            ubiprov = ubi_t[0:4]
                            ubidist = ubi_t[0:6]

                            departamento = self.env['res.country.state'].search(
                                [('code', '=', ubidepa), ('country_id', '=', pais.id)])
                            provincia = self.env['res.country.state'].search(
                                [('code', '=', ubiprov), ('country_id', '=', pais.id)])
                            distrito = self.env['res.country.state'].search(
                                [('code', '=', ubidist), ('country_id', '=', pais.id)])

                            state_id = departamento
                            province_id = provincia
                            district_id = distrito if distrito  else None




                    '''
                                        if tmp[0] == 'n1_estado':
                                            self.ruc_state = tmp[1]
                                        if tmp[0] == 'n1_condicion':
                                            self.ruc_condition = tmp[1]
                    '''
                return {'state': 'done',
                        'data':
                            {
                                'country_id': pais.id if pais else None,
                                'state_id': state_id.id if state_id else None,
                                'state_name': state_id.name if state_id else None,
                                'province_id': province_id.id if province_id else None,
                                'province_name': province_id.name if province_id else None,
                                'district_id': district_id.id if district_id else None,
                                'district_name': district_id.name if district_id else None,
                                'name': name,
                                'street':street,
                                'zip': zip
                            }
                        }

            else:
                return {'state':'error','msg':'El RUC es invalido.'}
        else:
            if not doctype.code_sunat == '1':
                return {'state': 'error', 'msg': 'Tipo de documento Invalido.'}
            result = None
            parameters = self.env['sale.main.parameter'].verify_query_parameters()
            if not vat:
                return {'state': 'error', 'msg': 'Debe seleccionar un DNI.'}
            client = Client(parameters.query_dni_url, faults=False, cachingpolicy=1, location=parameters.query_dni_url)
            try:
                result = client.service.consultar(str(vat), parameters.query_email, parameters.query_token,
                                                  parameters.query_type)
            except Exception as e:
                return {'state': 'error', 'msg': 'No se encontro el DNI'}
            if result:
                texto = result[1].split('|')

                nombres = ''
                a_paterno = ''
                a_materno = ''
                for c in texto:
                    tmp = c.split('=')
                    if tmp[0] == 'status_id' and tmp[1] == '102':
                        return {'state': 'error', 'msg': 'El DNI debe tener al menos 8 digitos de longitud'}
                    if tmp[0] == 'status_id' and tmp[1] == '103':
                        return {'state': 'error', 'msg': 'El DNI debe ser un valor numerico'}
                    if tmp[0] == 'reniec_nombres' and tmp[1] != '':
                        nombres = tmp[1]
                        # self.name_p = tmp[1]
                    if tmp[0] == 'reniec_paterno' and tmp[1] != '':
                        a_paterno = tmp[1]
                        # self.last_name = tmp[1]
                    if tmp[0] == 'reniec_materno' and tmp[1] != '':
                        a_materno = tmp[1]
                        # self.m_last_name = tmp[1]
                name = (nombres + " " + a_paterno + " " + a_materno).strip()
                return {'state': 'done',
                        'data':
                            {
                                'name': name,
                            }
                        }
            else:
                return {'state': 'error', 'msg': 'Tipo de documento Invalido.'}

####### CONSULTA RUC #########