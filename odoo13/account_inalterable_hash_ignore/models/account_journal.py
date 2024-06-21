# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	def write(self, vals):
		if 'restrict_mode_hash_table' in vals and not vals.get('restrict_mode_hash_table'):
			journal_entry = self.env['account.move'].search([('journal_id', '=', self.id), ('state', '=', 'posted'), ('secure_sequence_number', '!=', 0)])
			if len(journal_entry) > 0:
				for move in journal_entry:
					self.env.cr.execute("""UPDATE ACCOUNT_MOVE SET secure_sequence_number = Null where id = %d"""%(move.id))
		return super(AccountJournal, self).write(vals)