from odoo import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError
import base64


def find_uom_parent(uom_child):
    if uom_child and uom_child.category_id:
        for uom in uom_child.category_id.uom_ids:
            if uom.uom_type == 'reference':
                return uom
    return False


def find_data_return_qty_parent(uom_child, qty_child): # LO MISMO PERO SOLO DEVUELVE 1 VALOR
    uom_parent_id = find_uom_parent(uom_child)
    qty_done_parent = 0

    uom_child_id = uom_child
    qty_done_child = qty_child

    if uom_parent_id:
        # CHECK PARENT VALUE
        if uom_child == uom_parent_id:
            qty_done_parent = qty_child
        elif uom_child.uom_type == 'bigger':
            qty_done_parent = qty_child * uom_child.ratio
        elif uom_child.uom_type == 'smaller':
            qty_done_parent = (qty_child / uom_child.ratio) if uom_child.ratio != 0 else 0

    return qty_done_parent


def find_data_child_from_parent(qty_parent, uom_child):
    uom_parent_id = find_uom_parent(uom_child)
    qty_done_parent = qty_parent

    uom_child_id = uom_child
    qty_done_child = 0 # to find

    if uom_parent_id and uom_child_id:
        if uom_child_id == uom_parent_id:
            qty_done_child = qty_done_parent
        elif uom_child_id.uom_type == 'bigger':
            qty_done_child = qty_done_parent / uom_child_id.ratio if uom_child_id.ratio != 0 else 0
        elif uom_child_id.uom_type == 'smaller':
            qty_done_child = qty_done_parent * uom_child_id.ratio

    return qty_done_child


class ImportStockPriceLine(models.TransientModel):
	_name = 'import.stock.price.line'
	_description = 'Actulizar Saldos'

	name = fields.Char('name')
	picking_id = fields.Many2one('stock.picking', string='Transferencia')
	file = fields.Binary('Excel')
	name_file = fields.Char('name_file')
	
	stock_move_ids = fields.Many2many('stock.move', string='Movimientos de stock')

	crear_lote_si_no_existe = fields.Boolean('Crear Lote Si No Existe', default=False)
	forzar_actualizacion = fields.Boolean('Forzar Actualizacion', default=False)
	show_errors_quants = fields.Boolean('Show ERrors Quants', default=True)

	def check_lote(self, move_line, lot, errors, cont):
		if move_line.product_id.tracking not in ['serial', 'lot'] and lot not in [False, '']:
			errors += 'EN LA FILA %s EL PRODUCTO NO DEBE TENER LOTE\n\n' % (str(cont))

		lot = self.env['stock.production.lot'].sudo().search([
			('name', '=', str(lot)),
			('product_id', '=', move_line.product_id.id),
			('company_id', '=', move_line.company_id.id)
		])
		if not lot and not self.crear_lote_si_no_existe:
			errors += 'EN LA FILA %s NO EXISTE EL LOTE con producto %s \n\n'%(str(cont), move_line.product_id.name)
			return False, errors
		elif not lot and self.crear_lote_si_no_existe:
			lot = self.env['stock.production.lot'].sudo().create({
				'name': str(lot),
				'product_id': move_line.product_id.id,
				'company_id': move_line.company_id.id,
			})
			return lot, errors
		elif len(lot) > 1:
			errors += 'EN LA FILA %s SE ENCONTRO MAS DE 1 LOTE CON EL MISMO NOMBRE Y PRODUCTO\n\n' % (str(cont))
			return False, errors
		return lot, errors

	def update_uom(self):
		for move in self.picking_id.move_ids_without_package:
			if move.product_id:
				sql_1 = "UPDATE stock_move SET product_uom = %s, uom_child_id = %s WHERE id = %s" % (move.product_id.uom_id.id, move.product_id.uom_id.id, move.id)
				self.env.cr.execute(sql_1)
				# move.product_uom = move.product_id.uom_id.id
				# move.uom_child_id = move.product_id.uom_id.id
			for move_line in move.move_line_ids:
				if move_line.product_id:
					sql_2 = "UPDATE stock_move_line SET product_uom_id = %s, uom_child_id = %s WHERE id = %s" % (move_line.product_id.uom_id.id, move_line.product_id.uom_id.id, move_line.id)
					self.env.cr.execute(sql_2)
					# move_line.product_uom_id = move_line.product_id.uom_id.id
					# move_line.uom_child_id = move_line.product_id.uom_id.id

	def quants_change(self):
		errors = ''
		for move in self.picking_id.move_ids_without_package:
			for move_line in move.move_line_ids:
				if move_line.product_id:
					if move_line.lot_id:
						quants_total = self.env['stock.quant'].sudo().search([('product_id', '=', move_line.product_id.id), ('lot_id', '=', move_line.lot_id.id)])
						quant = self.env['stock.quant'].sudo().search([('product_id', '=', move_line.product_id.id), ('location_id', '=', move_line.location_id.id), ('lot_id', '=', move_line.lot_id.id)])
					else:
						quants_total = self.env['stock.quant'].sudo().search([('product_id', '=', move_line.product_id.id)])
						quant = self.env['stock.quant'].sudo().search([('product_id', '=', move_line.product_id.id), ('location_id', '=', move_line.location_id.id)])

					ubicaciones = self.env['stock.warehouse'].search([]).lot_stock_id
					ubicaciones_internas = self.env['stock.location'].search([('usage', '=', 'internal')])

					if not quant:
						temp_total = 0
						quant_to_modify = False
						for q in quants_total:
							temp_total += q.inventory_quantity_auto_apply
							if q.location_id in ubicaciones:
								quant_to_modify = q

						if not quant_to_modify:
							errors += 'EXTRAÑO: NO SE ENCONTRO EL QUANT %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)

						elif temp_total - move_line.qty_done < 0.01 and temp_total - move_line.qty_done > -0.01:
							dif = move_line.qty_done - temp_total

							quant_to_modify.inventory_quantity_auto_apply += dif
							quant_to_modify.available_quantity += dif
							quant_to_modify.quantity += dif

						else:
							check = temp_total - move_line.qty_done
							errors += 'NO SE ENCONTRO EL QUANT %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)


					elif quant and quant.inventory_quantity_auto_apply not in [move_line.qty_done * -1, move_line.qty_done]:
						if not quant:
							errors += 'NO SE ENCONTRO EL QUANT %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)
						elif len(quant) > 1:
							errors += 'SE ENCONTRO MAS DE 1 PRODUCTO %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)

						if quant:
							temp_total = 0
							for q in quants_total:
								temp_total += q.inventory_quantity_auto_apply
							# if temp_total != 0:
							if temp_total > 0.01 and temp_total < -0.01:
								errors += 'La sumatoria es diferente a 0 en el producto%s EN LA UBICACION %s CON EL LOTE %s TIENE SALDO\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)

							quant_ubi = []
							quant_ubi_inter = []
							for q in quants_total:
								if q == quant and q.inventory_quantity_auto_apply > 0:
									error += 'La cantidad es mayor a 0 del QUANT por producto %s EN LA UBICACION %s CON EL LOTE %s TIENE SALDO\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)
								elif q.location_id in ubicaciones:
									quant_ubi.append(q)
								elif q.location_id in ubicaciones_internas and q.location_id not in ubicaciones:
									quant_ubi_inter.append(q)

							if len(quant_ubi) > 1:
								for q in quant_ubi:
									q.location_id == move_line.location_dest_id
									quant_ubi = [q]
									break
							elif len(quant_ubi_inter) > 1:
								for q in quant_ubi_inter:
									q.location_id == move_line.location_dest_id
									quant_ubi_inter = [q]
									break
							elif len(quant_ubi_inter) == 0 and len(quant_ubi) == 0:
								errors += 'XAXAXA NO SE ENCONTRO EL QUANT %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)


							dif = move_line.qty_done - (quant.inventory_quantity_auto_apply * -1)

							quant.inventory_quantity_auto_apply -= dif
							quant.available_quantity -= dif
							quant.quantity -= dif

							if len(quant_ubi) == 1:
								quant_ubi[0].inventory_quantity_auto_apply += dif
								quant_ubi[0].available_quantity += dif
								quant_ubi[0].quantity += dif
							elif len(quant_ubi_inter) == 1:
								quant_ubi_inter[0].inventory_quantity_auto_apply += dif
								quant_ubi_inter[0].available_quantity += dif
								quant_ubi_inter[0].quantity += dif
							else:
								errors += 'DIFICIL NO SE ENCONTRO EL PRODUCTO %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)
				else:
					errors += 'NO HAY LOTE EN PRODUCTO %s EN LA UBICACION %s CON EL LOTE %s\n\n'%(move_line.product_id.name, move_line.location_id.name, move_line.lot_id.name)

					# move_line.quant_id.product_uom_id = move_line.product_id.uom_id.id
		if self.show_errors_quants:
			raise UserError(_(errors))

	def update_price(self):
		if self:
			try:
				file_string = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
				file_string.write(binascii.a2b_base64(self.file))
				file_string.close()
				book = xlrd.open_workbook(file_string.name)
				sheet = book.sheet_by_index(0)
			except:
				raise UserError(_("Por favor elija el archivo correcto"))
			starting_line = True
			cont=0
			errors = ''
			for i in range(sheet.nrows):
				if starting_line:
					starting_line = False
				else:
					line = list(sheet.row_values(i))
					cont += 1
					if self.env.context.get('type') == 'move':
						if line[0] or line[1]:
							stock_move = self.env['stock.move'].sudo().search([('id', '=', int(line[0]))])
							if not self.forzar_actualizacion:
									stock_move.price_unit_it = line[1]
							else:
								sql_query = "UPDATE stock_move SET price_unit_it = %s WHERE id = %d" % (str(line[1]), int(line[0]))
								self.env.cr.execute(sql_query)
						else:
							errors += 'EN LA FILA %s FALTA DATOS\n\n'%(str(cont))
					else:
						if self.picking_id.picking_type_id.code =='incoming':
							if line[0] or line[1] or line[2] or line[4] or line[5]:
								stock_move_line = self.env['stock.move.line'].sudo().search([('id', '=', int(line[0]))])

								if line[3]: # LOTE
									lot, errors = self.check_lote(stock_move_line, str(line[3]), errors, cont)
									if lot and self.forzar_actualizacion and stock_move_line.lot_id != lot:
										stock_move_line.lot_id = lot.id
									elif lot and not self.forzar_actualizacion and stock_move_line.lot_id != lot:
										sql_query = "UPDATE stock_move_line SET lot_id = %s WHERE id = %s" % (lot.id, stock_move_line.id)
										self.env.cr.execute(sql_query)

								if stock_move_line.product_id.tracking == 'serial' and line[4] == 0:
									errors += 'EN LA FILA %s EL PRODUCTO ES SERIAL Y NO PUEDE SER DIFERENTE A 1\n\n'%(str(cont))
								else:
									qty_parent = find_data_return_qty_parent(stock_move_line.uom_child_id, float(line[4]))
									if not self.forzar_actualizacion:
										if stock_move_line.qty_done_child != float(line[4]):
											stock_move_line.qty_done_child = float(line[4])
										if stock_move_line.qty_done != qty_parent:
											stock_move_line.qty_done = qty_parent
									else:
										sql_query = "UPDATE stock_move_line SET qty_done_child = %s, qty_done = %s WHERE id = %s\n\n" % (str(line[4]), str(qty_parent), str(stock_move_line.id))
										self.env.cr.execute(sql_query)


								if not self.forzar_actualizacion:
									stock_move_line.move_id.price_unit_it = line[5]
								else:
									sql_query = "UPDATE stock_move SET price_unit_it = %s WHERE id = %s" % (str(line[5]), str(stock_move_line.move_id.id))
									self.env.cr.execute(sql_query)

							else:
								errors += 'EN LA FILA %s FALTA DATOS\n\n'%(str(cont))
						else:
							errors += 'Solo disponible Para Tipo RECIBO'
			if errors != '':
				raise UserError(_(errors))

			if not self.forzar_actualizacion and self.picking_id.picking_type_id.code =='incoming':
				for move in self.picking_id.move_ids_without_package:
					qty_odoo = 0
					qty_ferco = 0
					for move_line in move.move_line_ids:
						qty_odoo += move_line.qty_done
						qty_ferco += move_line.qty_done_child
					move.product_uom_qty = qty_odoo
					move.qty_demanded_child = qty_ferco
					move.qty_done_child = qty_ferco

			elif self.forzar_actualizacion and self.picking_id.picking_type_id.code =='incoming':
				for move in self.picking_id.move_ids_without_package:
					qty_odoo = 0
					qty_ferco = 0
					for move_line in move.move_line_ids:
						qty_odoo += move_line.qty_done
						qty_ferco += move_line.qty_done_child
					sql_query = "UPDATE stock_move SET product_uom_qty = %s, qty_demanded_child = %s, qty_done_child = %s WHERE id = %s" % (str(qty_odoo), str(qty_ferco), str(qty_ferco), str(move.id))
					self.env.cr.execute(sql_query)



			return self.env['popup.it'].get_message('SE ACTUALIZÓ CORRECTAMENTE SUS REGISTROS')


	def download_template(self):
		for i in self:
			if i.picking_id:
				picking_id = self.picking_id.id
				return {
					'type' : 'ir.actions.act_url',
					'url': '/web/binary/download_template_update_price_stock_picking_id/%d' % picking_id,
					'target': 'new',
					}
			stock_move_ids = []
			if i.stock_move_ids:
				for stock in i.stock_move_ids:
					stock_move_ids.append(stock.id)
			return {
					'type' : 'ir.actions.act_url',
					'url': '/web/binary/download_template_update_price_stock_moves/%s' % stock_move_ids,
					'target': 'new',
					}
