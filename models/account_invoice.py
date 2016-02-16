# -*- coding: utf-8 -*-############################################################################### For copyright and license notices, see __openerp__.py file in root directory##############################################################################from openerp import models, fields, api, exceptions, _from openerp import netsvc,workflowimport datetimeclass account_invoice(models.Model):	# _name = "account.invoice"	_inherit = "account.invoice"	#picking_ids = fields.One2many('stock.picking', 'invoice_id', 'Related Pickings', readonly=True,help="Related pickings (only when the invoice has been generated from the picking).")	immediate = fields.Boolean('Fattura Immediata', readonly=True)	dataora = fields.Datetime('Data e ora trasporto')	payment_term = fields.Many2one('account.payment.term', 'Payment Term')	partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address', readonly=True,										 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},										 help="Invoice address for current sales order.")	partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True,										  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},										  help="Delivery address for current sales order.")	carriage_condition_id = fields.Many2one('stock.incoterms', 'Incoterms')	goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of Goods')	transportation_reason_id = fields.Many2one('stock.picking.transportation_reason', 'Reason for Transportation')	transportation_method_id = fields.Many2one('stock.picking.transportation_method', 'Method of Transportation')	carrier_id = fields.Many2one('delivery.carrier', string='Carrier')	workflow_process_id = fields.Many2one('sale.workflow.process', string='Sale Workflow Process')	sale_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', string='Sale Orders')	number_of_packages = fields.Integer('Number of packages')    #	# def _get_payment(self, cr, uid, invoice, context=None):	# 	if invoice.type == "out_invoice" and invoice.sale_ids:	# 		return invoice.sale_ids[0].payment_ids	# 	return []    #	# def _can_be_reconciled(self, cr, uid, invoice, context=None):	# 	payments = self._get_payment(cr, uid, invoice, context=context)	# 	if not (payments and invoice.move_id):	# 		return False	# 		# Check currency	# 	company_currency_id = invoice.company_id.currency_id.id	# 	for payment in payments:	# 		currency_id = payment.currency_id.id or company_currency_id	# 		if currency_id != invoice.currency_id.id:	# 			return False	# 	return True    #	# def _get_sum_invoice_move_line(self, cr, uid, move_lines, invoice_type, context=None):	# 	if invoice_type in ['in_refund', 'out_invoice']:	# 		line_type = 'debit'	# 	else:	# 		line_type = 'credit'	# 	return self._get_sum_move_line(cr, uid, move_lines, line_type, context=None)    #	# def _get_sum_payment_move_line(self, cr, uid, move_lines, invoice_type, context=None):	# 	if invoice_type in ['in_refund', 'out_invoice']:	# 		line_type = 'credit'	# 	else:	# 		line_type = 'debit'	# 	return self._get_sum_move_line(cr, uid, move_lines, line_type, context=None)    #    #	# def _get_sum_move_line(self, cr, uid, move_lines, line_type, context=None):	# 	res = {	# 		'max_date': False,	# 		'line_ids': [],	# 		'total_amount': 0,	# 		'total_amount_currency': 0,	# 	}	# 	for move_line in move_lines:	# 		if move_line[line_type] > 0:	# 			if move_line.date > res['max_date']:	# 				res['max_date'] = move_line.date	# 			res['line_ids'].append(move_line.id)	# 			res['total_amount'] += move_line[line_type]	# 			res['total_amount_currency'] += move_line.amount_currency	# 	return res    #	# def _prepare_write_off(self, cr, uid, invoice, res_invoice, res_payment, context=None):	# 	if context is None:	# 		context = {}	# 	ctx = context.copy()	# 	if res_invoice['total_amount'] - res_payment['total_amount'] > 0:	# 		writeoff_type = 'expense'	# 	else:	# 		writeoff_type = 'income'	# 	account_id, journal_id = invoice.company_id.get_write_off_information('exchange', writeoff_type,	# 																		  context=context)	# 	max_date = max(res_invoice['max_date'], res_payment['max_date'])	# 	ctx['p_date'] = max_date	# 	period_obj = self.pool.get('account.period')	# 	period_id = period_obj.find(cr, uid, max_date, context=context)[0]	# 	return {	# 		'type': 'auto',	# 		'writeoff_acc_id': account_id,	# 		'writeoff_period_id': period_id,	# 		'writeoff_journal_id': journal_id,	# 		'context': ctx,	# 	}    #	# def _reconcile_invoice(self, cr, uid, invoice, context=None):	# 	move_line_obj = self.pool.get('account.move.line')	# 	currency_obj = self.pool.get('res.currency')	# 	is_zero = currency_obj.is_zero	# 	company_currency_id = invoice.company_id.currency_id.id	# 	currency = invoice.currency_id	# 	use_currency = currency.id != company_currency_id	# 	if self._can_be_reconciled(cr, uid, invoice, context=context):	# 		payment_move_lines = []	# 		payment_move_lines = self._get_payment(cr, uid, invoice, context=context)	# 		res_payment = self._get_sum_payment_move_line(cr, uid, payment_move_lines, invoice.type, context=context)	# 		res_invoice = self._get_sum_invoice_move_line(cr, uid, invoice.move_id.line_id, invoice.type,	# 													  context=context)	# 		line_ids = res_invoice['line_ids'] + res_payment['line_ids']	# 		if not use_currency:	# 			balance = abs(res_invoice['total_amount'] -	# 						  res_payment['total_amount'])	# 			if line_ids and is_zero(cr, uid, currency, balance):	# 				move_line_obj.reconcile(cr, uid, line_ids, context=context)	# 		else:	# 			balance = abs(res_invoice['total_amount_currency'] -	# 						  res_payment['total_amount_currency'])	# 			if line_ids and is_zero(cr, uid, currency, balance):	# 				kwargs = self._prepare_write_off(cr, uid,	# 												 invoice,	# 												 res_invoice,	# 												 res_payment,	# 												 context=context)	# 				move_line_obj.reconcile(cr, uid, line_ids, **kwargs)    #	# def reconcile_invoice(self, cr, uid, ids, context=None):	# 	""" Simple method to reconcile the invoice with the payment	# 	generated on the sale order """	# 	if not isinstance(ids, (list, tuple)):	# 		ids = [ids]	# 	for invoice in self.browse(cr, uid, ids, context=context):	# 		self._reconcile_invoice(cr, uid, invoice, context=context)	# 	return True    #    #	def get_salenote(self, cr, uid, ids, partner_id, context=None):	 	context_lang = context.copy()	 	if partner_id:	 		partner_lang = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context).lang	 		context_lang.update({'lang': partner_lang})	 	return self.pool.get('res.users').browse(cr, uid, uid, context=context_lang).company_id.sale_note	def _get_default_company(self, cr, uid, context=None):	 	company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)	 	#if not company_id:	 	#raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))	 	return company_id	def onchange_delivery_id(self, cr, uid, ids, company_id, partner_id, delivery_id, fiscal_position, context=None):		r = {'value': {}}		if not fiscal_position:			if not company_id:				company_id = self._get_default_company(cr, uid, context=context)			fiscal_position = self.pool['account.fiscal.position'].get_fiscal_position(cr, uid, company_id, partner_id,																					   delivery_id, context=context)			if fiscal_position:				r['value']['fiscal_position'] = fiscal_position		return r	# def onchange_partner_id(self, cr, uid, ids, part, partner_id, partner_invoice_id, partner_shipping_id, payment_term,	# 						fiscal_position, company_id, context=None):	# 	super(account_invoice,self).onchange_partner_id( cr, uid, ids, type, partner_id,	def onchange_partner_id(self, cr, uid, ids, type, partner_id,                            date_invoice=False, payment_term=False,                            partner_bank_id=False, company_id=False):		res = super(account_invoice, self).onchange_partner_id(			cr, uid, ids, type, partner_id,			date_invoice=date_invoice, payment_term=payment_term,			partner_bank_id=partner_bank_id, company_id=company_id)		if not partner_id:			return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'payment_term': False,							  'fiscal_position': False}}		part = self.pool.get('res.partner').browse(cr, uid, partner_id)		addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])		pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False		payment_term = part.property_payment_term and part.property_payment_term.id or False		dedicated_salesman = part.user_id and part.user_id.id or uid		val = {			'partner_invoice_id': addr['invoice'],			'partner_shipping_id': addr['delivery'],			'payment_term': payment_term,			'user_id': dedicated_salesman,			'account_id': part.property_account_receivable,			'date_invoice': datetime.date.today(),		}		delivery_onchange = self.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,													  context=context)		val.update(delivery_onchange['value'])		if pricelist:			val['pricelist_id'] = pricelist		sale_note = self.get_salenote(cr, uid, ids, part.id, context=context)		if sale_note: val.update({'note': sale_note})		return {'value': val}	@api.multi	def action_cancel(self):		for self in self:			moves = self.env['account.move']			for inv in self:				if inv.move_id:					moves += inv.move_id				if inv.payment_ids:					for move_line in inv.payment_ids:						if move_line.reconcile_partial_id.line_partial_ids:							raise exceptions.Warning(_('Error!'), _(								'You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))			self.mapped('invoice_line.picking_id').write({'invoice_state': '2binvoiced'})			# First, set the invoices as cancelled and detach the move ids			#self.write({'state': 'cancel', 'move_id': False, 'internal_number': ''})			# delete the move this invoice was pointing to			# Note that the corresponding move_lines and move_reconciles			# will be automatically deleted too			if moves:				# second, invalidate the move(s)				moves.button_cancel()			self.env.cr.execute('select order_id from sale_order_invoice_rel  where invoice_id = %s' % (self.id))			sale_ids = self.env.cr.fetchall()			for sale_id in sale_ids:				sale_obj = self.env['sale.order'].browse(sale_id)				for sale_id in sale_obj:					sale_id.write({'state': 'progress','internal_invoice_number':self.internal_number,})					picking = self.env['stock.picking'].search([('origin', '=', sale_id.name)])					sale_id.write({'is_modify':True})					for pick in picking:						picki_obj = self.env['stock.picking'].browse(pick.id)						context = {}						context.update({'active_id': pick.id})						ret = self.pool.get('stock.return.picking').create(self._cr,self._uid,{'invoice_state':'2binvoiced'})						pick.write({'state': 'draft'})						#pick.unlink()						self.pool.get('stock.return.picking').createreturns(self._cr,self._uid, [ret],context)						move_obj = self.env['stock.move'].search([('picking_id', '=', pick.id)])						for move_ids in move_obj:							move_ids.write({'state': 'draft'})			account_move_id = self.env['account.invoice'].search([('id', '=', self.id)]).move_id		super(account_invoice, self).action_cancel()	@api.multi	def action_move_create(self):		""" Creates invoice related analytics and financial move lines """		account_invoice_tax = self.env['account.invoice.tax']		account_move = self.env['account.move']		for inv in self:			print "inv",inv			if not inv.journal_id.sequence_id:				raise exceptions.Warning(_('Error!'), _('Please define sequence on the journal related to this invoice.'))			if not inv.invoice_line:				raise exceptions.Warning(_('No Invoice Lines!'), _('Please create some invoice lines.'))			if inv.move_id:				continue			ctx = dict(self._context, lang=inv.partner_id.lang)			if not inv.date_invoice:				inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})			date_invoice = inv.date_invoice			company_currency = inv.company_id.currency_id			# create the analytical lines, one move line per invoice line			iml = inv._get_analytic_lines()			print "iml",iml			# check if taxes are all computed			compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))			inv.check_tax_lines(compute_taxes)			print "compute_taxes",compute_taxes			# I disabled the check_total feature			if self.env.user.has_group('account.group_supplier_inv_check_total'):				if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):					raise exceptions.Warning(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))			if inv.payment_term:				total_fixed = total_percent = 0				for line in inv.payment_term.line_ids:					if line.value == 'fixed':						total_fixed += line.value_amount					if line.value == 'procent':						total_percent += line.value_amount				total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)				if (total_fixed + total_percent) > 100:					raise exceptions.Warning(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))			# one move line per tax line			iml += account_invoice_tax.move_line_get(inv.id)			if inv.type in ('in_invoice', 'in_refund'):				ref = inv.reference			else:				ref = inv.number			diff_currency = inv.currency_id != company_currency			# create one move line for the total and possibly adjust the other lines amount			total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)			name = inv.supplier_invoice_number or inv.name or '/'			totlines = []			if inv.payment_term:				totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]			if totlines:				res_amount_currency = total_currency				ctx['date'] = date_invoice				for i, t in enumerate(totlines):					if inv.currency_id != company_currency:						amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)					else:						amount_currency = False					# last line: add the diff					res_amount_currency -= amount_currency or 0					if i + 1 == len(totlines):						amount_currency += res_amount_currency					iml.append({						'type': 'dest',						'name': name,						'price': t[1],						'account_id': inv.account_id.id,						'date_maturity': t[0],						'amount_currency': diff_currency and amount_currency,						'currency_id': diff_currency and inv.currency_id.id,						'ref': ref,					})			else:				iml.append({					'type': 'dest',					'name': name,					'price': total,					'account_id': inv.account_id.id,					'date_maturity': inv.date_due,					'amount_currency': diff_currency and total_currency,					'currency_id': diff_currency and inv.currency_id.id,					'ref': ref				})			date = date_invoice			part = self.env['res.partner']._find_accounting_partner(inv.partner_id)			line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]			line = inv.group_lines(iml, line)			journal = inv.journal_id.with_context(ctx)			if journal.centralisation:				raise exceptions.Warning(_('User Error!'),						_('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))			line = inv.finalize_invoice_move_lines(line)			move_vals = {				'ref': inv.reference or inv.supplier_invoice_number or inv.name,				'line_id': line,				'journal_id': journal.id,				'date': inv.date_invoice,				'narration': inv.comment,				'company_id': inv.company_id.id,			}			ctx['company_id'] = inv.company_id.id			period = inv.period_id			if not period:				period = period.with_context(ctx).find(date_invoice)[:1]			if period:				move_vals['period_id'] = period.id				for i in line:					i[2]['period_id'] = period.id			ctx['invoice'] = inv			ctx_nolang = ctx.copy()			ctx_nolang.pop('lang', None)			move = account_move.with_context(ctx_nolang).create(move_vals)			print "move_vals",move_vals			# make the invoice point to that move			vals = {				'move_id': move.id,				'period_id': period.id,				'move_name': move.name,			}			inv.with_context(ctx).write(vals)			print "ctx",ctx			print "vals",vals			# Pass invoice in context in method post: used if you want to get the same			# account move reference when creating the same invoice after a cancelled one:			move.post()		self._log_event()		return Trueclass AccountInvoiceLine(models.Model):	_inherit = 'account.invoice.line'	move = fields.Many2one('stock.move', string='Stock Move')	picking_id = fields.Many2one(		string='Picking', comodel_name='stock.picking',		related='move.picking_id', readonly=True)