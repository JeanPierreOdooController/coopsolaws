# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import urllib.request
import urllib.parse
import requests
import json
import urllib3
from datetime import datetime, timedelta

class AccountMove(models.Model):
	_inherit = 'account.move'

	query_sunat_ids = fields.One2many('account.query.sunat','move_id',string=u'Verificacion Sunat',copy=False)

	def action_verify_sunat_invoice(self):
		obj_query = self.env['account.query.sunat']
		param = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if not param:
			raise UserError(u'No existen Parametros Principales de Contabilidad para su Compañía')
		
		if not param.client_id or not param.client_secret:
			raise UserError(u'No estan configuradas las credenciales generadas en la página de SUNAT en Parametros Principales de Contabilidad para su Compañía')

		today = datetime.now()

		if not param.token_expire or today>param.token_expiration_date:
			params = {"grant_type" : u"client_credentials",
					"scope": u"https://api.sunat.gob.pe/v1/contribuyente/contribuyentes",
					"client_id": param.client_id,
					"client_secret": param.client_secret}

			url = 'https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/'.format(client_id = param.client_id)
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/x-www-form-urlencoded'
			headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
			try:
				r = requests.post(url, headers=headers, data=params)
				#raise UserError(r.text)
				arre = r.text.replace("'",'"')
				arr2 = json.loads(arre)
				if 'access_token' in arr2.keys():
					param.token_expire = arr2['access_token']
					param.token_generation_date = today
					param.token_expiration_date = today + timedelta(seconds=int(arr2['expires_in']))
			except Exception as err:
				raise UserError(err)

		for move in self:
			if move.type not in ('in_invoice','in_refund'):
				raise UserError('Solo se aplica en Facturas de Proveedor')
			partition = move.ref.split('-')
			params = {
						"numRuc": move.partner_id.vat,
						"codComp": move.type_document_id.code,
						"numeroSerie": partition[0],
						"numero": int(partition[1]),
						"fechaEmision": move.invoice_date.strftime('%d/%m/%Y'),
						"monto": move.amount_total
					}
			
			url = 'https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/{ruc}/validarcomprobante'.format(ruc = move.company_id.partner_id.vat)
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/json'
			headers['Authorization'] = 'Bearer ' + param.token_expire 
			headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
			arr2={}
			try:
				r = requests.post(url, headers=headers, data=json.dumps(params))
				arre = r.text.replace("'",'"')
				arr2 = json.loads(arre)

			except Exception as err:
				raise UserError(err)
			if 'success' in arr2.keys():
				reg = obj_query.search([('move_id','=',move.id)],limit=1)
				if arr2['success']:
					if reg:
						reg.write({
							'success': arr2['success'],
							'message': arr2['message'] or '',
							'estadocp': arr2['data']['estadoCp'] if 'estadoCp' in arr2['data'].keys() else '',
							'estadoruc': arr2['data']['estadoRuc'] if 'estadoRuc' in arr2['data'].keys() else '',
							'conddomiruc': arr2['data']['condDomiRuc'] if 'condDomiRuc' in arr2['data'].keys() else '',
							'observaciones': arr2['data']['observaciones']  if 'observaciones' in arr2['data'].keys() else '',
						})
					else:
						obj_query.create({
							'move_id': move.id,
							'success': arr2['success'],
							'message': arr2['message'] or '',
							'estadocp': arr2['data']['estadoCp'] if 'estadoCp' in arr2['data'].keys() else '',
							'estadoruc': arr2['data']['estadoRuc'] if 'estadoRuc' in arr2['data'].keys() else '',
							'conddomiruc': arr2['data']['condDomiRuc'] if 'condDomiRuc' in arr2['data'].keys() else '',
							'observaciones': arr2['data']['observaciones']  if 'observaciones' in arr2['data'].keys() else '',
						})
				else:
					if reg:
						reg.write({
							'success': arr2['success'] or False,
							'message': arr2['message'] or '',
							'errorcode': arr2['errorCode'] or '',
						})
					else:
						obj_query.create({
							'move_id': move.id,
							'success': arr2['success'] or False,
							'message': arr2['message'] or '',
							'errorcode': arr2['errorCode'] or '',
						})
		return self.env['popup.it'].get_message('Se realizaron las consultas exitosamente.')