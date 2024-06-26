# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError
import csv
import base64
import io as StringIO
import xlrd
from odoo.tools import ustr
import logging


_logger = logging.getLogger(__name__)


class import_pol_wizard(models.TransientModel):
	_name = "import.pol.wizard"
	_description = "Import Purchase Order Line Wizard"       

	import_type = fields.Selection([
		('csv', 'CSV File'),
		('excel', 'Excel File')
		], default="excel", string="Import File Type", required=True)
	file = fields.Binary(string="File")   
	product_by = fields.Selection([
		('name', 'Name'),
		('int_ref', 'Internal Reference'),
		('barcode', 'Barcode')
		], default="name", string="Product By", required=True) 
	
	def validate_field_value(self, field_name, field_ttype, field_value, field_required,field_name_m2o):
		""" Validate field value, depending on field type and given value """
		self.ensure_one()

		try:       
			checker = getattr(self, 'validate_field_' + field_ttype)
		except AttributeError:
			_logger.warning(field_ttype + ": This type of field has no validation method")
			return {}
		else:
			return checker(field_name, field_ttype, field_value, field_required, field_name_m2o)    

	def show_success_msg(self, counter, skipped_line_no):
		
		# to close the current active wizard        
		action = self.env.ref('import_purchase_order_line.sh_import_pol_action').read()[0]
		action = {'type': 'ir.actions.act_window_close'} 
		
		# open the new success message box    
		#view = self.env.ref('sh_message.sh_message_wizard')
		#view_id = view and view.id or False                                   
		context = dict(self._context or {})
		dic_msg = str(counter) + " Records imported successfully"
		if skipped_line_no:
			dic_msg = dic_msg + "\nNote:"
		for k, v in skipped_line_no.items():
			dic_msg = dic_msg + "\nRow No " + k + " " + v + " "
		context['message'] = dic_msg     

		return self.env['popup.it'].get_message(dic_msg)
	
	def import_pol_apply(self):
		pol_obj = self.env['purchase.order.line']
		ir_model_fields_obj = self.env['ir.model.fields']
		
		# perform import lead
		if self and self.file and self.env.context.get('sh_po_id', False):
			# For Excel
			if self.import_type == 'excel':
				counter = 1
				skipped_line_no = {}
				row_field_dic = {}
				row_field_error_dic = {}                      
				try:
					wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
					sheet = wb.sheet_by_index(0)     
					skip_header = True    
					for row in range(sheet.nrows):
						try:
							if skip_header:
								skip_header = False
								
								for i in range(7, sheet.ncols):
									name_field = sheet.cell(row,i).value
									name_m2o = False
									if '@' in sheet.cell(row,i).value:
										list_field_str = name_field.split('@')
										name_field = list_field_str[0]   
										name_m2o   = list_field_str[1]               
									search_field = ir_model_fields_obj.sudo().search([
										("model", "=", "purchase.order.line"),
										("name", "=", name_field),
										("store", "=", True),
										], limit = 1)
									if search_field:
										field_dic = {
											'name' : name_field,
											'ttype': search_field.ttype,
											'required': search_field.required,
											'name_m2o':name_m2o
											}
										row_field_dic.update({i : field_dic})  
									else:
										row_field_error_dic.update({sheet.cell(row,i).value : " - field not found"})                                                                
								
								counter = counter + 1
								continue
							
							if sheet.cell(row, 0).value != '': 
								vals = {}
								
								field_nm = 'name'
								if self.product_by == 'name':
									field_nm = 'name'
								elif self.product_by == 'int_ref':
									field_nm = 'default_code'
								elif self.product_by == 'barcode':
									field_nm = 'barcode'
								
								search_product = self.env['product.product'].search([(field_nm, '=', sheet.cell(row, 0).value)], limit=1)
								if search_product:
									vals.update({'product_id' : search_product.id})
									
									if sheet.cell(row, 1).value != '':
										vals.update({'name' : sheet.cell(row, 1).value })
									else:
										vals.update({'name' : search_product.name})
										
										active_po = self.env['purchase.order'].search([('id', '=', self.env.context.get('sh_po_id'))])
										if active_po:
											product_lang = search_product.with_context({
												'lang': active_po.partner_id.lang,
												'partner_id': active_po.partner_id.id,
											})
											pro_desc = product_lang.display_name
											if product_lang.description_purchase:
												pro_desc += '\n' + product_lang.description_purchase 
											vals.update({'name' : pro_desc})                                       

									if sheet.cell(row, 2).value != '':
										vals.update({'product_qty' : sheet.cell(row, 2).value })
									else:
										vals.update({'product_qty' : 1 })
									
									if sheet.cell(row, 3).value in (None, "") and search_product.uom_po_id:
										vals.update({'product_uom' : search_product.uom_po_id.id })
									else:
										search_uom = self.env['uom.uom'].search([('name', '=', sheet.cell(row, 3).value)], limit=1) 
										if search_uom:
											vals.update({'product_uom' : search_uom.id })
										else:
											skipped_line_no[str(counter)] = " - Unit of Measure not found. " 
											counter = counter + 1
											continue
									
									if sheet.cell(row, 4).value in (None, ""):
										vals.update({'price_unit' : search_product.standard_price })
									else:
										vals.update({'price_unit' : sheet.cell(row, 4).value })
										
									if sheet.cell(row, 5).value.strip() in (None, "") and search_product.supplier_taxes_id:
										vals.update({'taxes_id' : [(6, 0, search_product.supplier_taxes_id.ids)]})
									else:
										taxes_list = []
										some_taxes_not_found = False
										for x in sheet.cell(row, 5).value.split(','):
											x = x.strip()
											if x != '':
												search_tax = self.env['account.tax'].search([('name', '=', x)], limit=1)
												if search_tax:
													taxes_list.append(search_tax.id)
												else:
													some_taxes_not_found = True
													skipped_line_no[str(counter)] = " - Taxes " + x + " not found. "                                                 
													break  
										if some_taxes_not_found:
											counter = counter + 1
											continue
										else:
											vals.update({'taxes_id' : [(6, 0, taxes_list)]})

									if sheet.cell(row, 7).value not in (None, ""):
										active_po = self.env['purchase.order'].search([('id', '=', self.env.context.get('sh_po_id'))])
										search_analytic = self.env['account.analytic.account'].search([('code', '=', sheet.cell(row, 7).value),('company_id','=',active_po.company_id.id)], limit=1) 
										if search_analytic:
											vals.update({'account_analytic_id' : search_analytic.id })
										else:
											skipped_line_no[str(counter)] = " - Analytic Account not found. " 
											counter = counter + 1
											continue
									
									if sheet.cell(row, 8).value.strip() in (None, ""):
										vals.update({'analytic_tag_ids' : []})
									else:
										active_po = self.env['purchase.order'].search([('id', '=', self.env.context.get('sh_po_id'))])
										tag_list = []
										some_tag_not_found = False
										for x in sheet.cell(row, 8).value.split(','):
											x = x.strip()
											if x != '':
												search_tax = self.env['account.analytic.tag'].search([('name', '=', x),('company_id','=',active_po.company_id.id)], limit=1)
												if search_tax:
													tag_list.append(search_tax.id)
												else:
													some_tag_not_found = True
													skipped_line_no[str(counter)] = " - Analytic Tags " + x + " not found in company. "                                                 
													break  
										if some_tag_not_found:
											counter = counter + 1
											continue
										else:
											vals.update({'analytic_tag_ids' : [(6, 0, tag_list)]})
									
									if sheet.cell(row, 6).value in (None, ""):
										vals.update({'date_planned' : datetime.now()})
									else:
										cd = sheet.cell(row, 6).value               
										cd = str(datetime.strptime(cd, '%Y-%m-%d').date())
										vals.update({"date_planned" : cd})  
										
								else:
									skipped_line_no[str(counter)] = " - Product not found. " 
									counter = counter + 1 
									continue
								
								vals.update({'order_id' : self.env.context.get('sh_po_id')})
								
								
								is_any_error_in_dynamic_field = False
								for k_row_index, v_field_dic in row_field_dic.items():
									
									field_name = v_field_dic.get("name")
									field_ttype = v_field_dic.get("ttype")
									field_value = sheet.cell(row,k_row_index).value
									field_required = v_field_dic.get("required")
									field_name_m2o = v_field_dic.get("name_m2o")
										
									dic =  self.validate_field_value(field_name, field_ttype, field_value, field_required,field_name_m2o)
									if dic.get("error",False):
										skipped_line_no[str(counter)] = dic.get("error")                                         
										is_any_error_in_dynamic_field = True
										break
									else:
										vals.update(dic)
								
								if is_any_error_in_dynamic_field:
									counter = counter + 1
									continue
								
								created_pol = pol_obj.create(vals)
								counter = counter + 1
							
							else:
								skipped_line_no[str(counter)] = " - Product is empty. "  
								counter = counter + 1      
						
						except Exception as e:
							skipped_line_no[str(counter)] = " - Value is not valid " + ustr(e)   
							counter = counter + 1 
							continue          
							 
				except Exception:
					raise UserError(_("Sorry, Your excel file does not match with our format"))
				 
				if counter > 1:
					completed_records = (counter - len(skipped_line_no)) - 2
					res = self.show_success_msg(completed_records, skipped_line_no)
					return res

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_purchase_line',
			 'target': 'new',
			 }