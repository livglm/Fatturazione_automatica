# -*- coding: utf-8 -*-############################################################################### For copyright and license notices, see __openerp__.py file in root directory##############################################################################from openerp import models, fields, api, exceptions, _from openerp import netsvc,workflowimport datetimeclass account_invoice(models.Model):	# _name = "account.invoice"	_inherit = "account.invoice"	#picking_ids = fields.One2many('stock.picking', 'invoice_id', 'Related Pickings', readonly=True,help="Related pickings (only when the invoice has been generated from the picking).")	immediate = fields.Boolean('Fattura Immediata', readonly=True)	dataora = fields.Datetime('Data e ora trasporto')	payment_term = fields.Many2one('account.payment.term', 'Payment Term')	partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address', readonly=True,										 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},										 help="Invoice address for current sales order.")	partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True,										  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},										  help="Delivery address for current sales order.")	carriage_condition_id = fields.Many2one('stock.incoterms', 'Incoterms')	goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of Goods')	transportation_reason_id = fields.Many2one('stock.picking.transportation_reason', 'Reason for Transportation')	transportation_method_id = fields.Many2one('stock.picking.transportation_method', 'Method of Transportation')	carrier_id = fields.Many2one('delivery.carrier', string='Carrier')	workflow_process_id = fields.Many2one('sale.workflow.process', string='Sale Workflow Process')	sale_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', string='Sale Orders')    #	# def _get_payment(self, cr, uid, invoice, context=None):	# 	if invoice.type == "out_invoice" and invoice.sale_ids:	# 		return invoice.sale_ids[0].payment_ids	# 	return []    #	# def _can_be_reconciled(self, cr, uid, invoice, context=None):	# 	payments = self._get_payment(cr, uid, invoice, context=context)	# 	if not (payments and invoice.move_id):	# 		return False	# 		# Check currency	# 	company_currency_id = invoice.company_id.currency_id.id	# 	for payment in payments:	# 		currency_id = payment.currency_id.id or company_currency_id	# 		if currency_id != invoice.currency_id.id:	# 			return False	# 	return True    #	# def _get_sum_invoice_move_line(self, cr, uid, move_lines, invoice_type, context=None):	# 	if invoice_type in ['in_refund', 'out_invoice']:	# 		line_type = 'debit'	# 	else:	# 		line_type = 'credit'	# 	return self._get_sum_move_line(cr, uid, move_lines, line_type, context=None)    #	# def _get_sum_payment_move_line(self, cr, uid, move_lines, invoice_type, context=None):	# 	if invoice_type in ['in_refund', 'out_invoice']:	# 		line_type = 'credit'	# 	else:	# 		line_type = 'debit'	# 	return self._get_sum_move_line(cr, uid, move_lines, line_type, context=None)    #    #	# def _get_sum_move_line(self, cr, uid, move_lines, line_type, context=None):	# 	res = {	# 		'max_date': False,	# 		'line_ids': [],	# 		'total_amount': 0,	# 		'total_amount_currency': 0,	# 	}	# 	for move_line in move_lines:	# 		if move_line[line_type] > 0:	# 			if move_line.date > res['max_date']:	# 				res['max_date'] = move_line.date	# 			res['line_ids'].append(move_line.id)	# 			res['total_amount'] += move_line[line_type]	# 			res['total_amount_currency'] += move_line.amount_currency	# 	return res    #	# def _prepare_write_off(self, cr, uid, invoice, res_invoice, res_payment, context=None):	# 	if context is None:	# 		context = {}	# 	ctx = context.copy()	# 	if res_invoice['total_amount'] - res_payment['total_amount'] > 0:	# 		writeoff_type = 'expense'	# 	else:	# 		writeoff_type = 'income'	# 	account_id, journal_id = invoice.company_id.get_write_off_information('exchange', writeoff_type,	# 																		  context=context)	# 	max_date = max(res_invoice['max_date'], res_payment['max_date'])	# 	ctx['p_date'] = max_date	# 	period_obj = self.pool.get('account.period')	# 	period_id = period_obj.find(cr, uid, max_date, context=context)[0]	# 	return {	# 		'type': 'auto',	# 		'writeoff_acc_id': account_id,	# 		'writeoff_period_id': period_id,	# 		'writeoff_journal_id': journal_id,	# 		'context': ctx,	# 	}    #	# def _reconcile_invoice(self, cr, uid, invoice, context=None):	# 	move_line_obj = self.pool.get('account.move.line')	# 	currency_obj = self.pool.get('res.currency')	# 	is_zero = currency_obj.is_zero	# 	company_currency_id = invoice.company_id.currency_id.id	# 	currency = invoice.currency_id	# 	use_currency = currency.id != company_currency_id	# 	if self._can_be_reconciled(cr, uid, invoice, context=context):	# 		payment_move_lines = []	# 		payment_move_lines = self._get_payment(cr, uid, invoice, context=context)	# 		res_payment = self._get_sum_payment_move_line(cr, uid, payment_move_lines, invoice.type, context=context)	# 		res_invoice = self._get_sum_invoice_move_line(cr, uid, invoice.move_id.line_id, invoice.type,	# 													  context=context)	# 		line_ids = res_invoice['line_ids'] + res_payment['line_ids']	# 		if not use_currency:	# 			balance = abs(res_invoice['total_amount'] -	# 						  res_payment['total_amount'])	# 			if line_ids and is_zero(cr, uid, currency, balance):	# 				move_line_obj.reconcile(cr, uid, line_ids, context=context)	# 		else:	# 			balance = abs(res_invoice['total_amount_currency'] -	# 						  res_payment['total_amount_currency'])	# 			if line_ids and is_zero(cr, uid, currency, balance):	# 				kwargs = self._prepare_write_off(cr, uid,	# 												 invoice,	# 												 res_invoice,	# 												 res_payment,	# 												 context=context)	# 				move_line_obj.reconcile(cr, uid, line_ids, **kwargs)    #	# def reconcile_invoice(self, cr, uid, ids, context=None):	# 	""" Simple method to reconcile the invoice with the payment	# 	generated on the sale order """	# 	if not isinstance(ids, (list, tuple)):	# 		ids = [ids]	# 	for invoice in self.browse(cr, uid, ids, context=context):	# 		self._reconcile_invoice(cr, uid, invoice, context=context)	# 	return True    #    #	def get_salenote(self, cr, uid, ids, partner_id, context=None):	 	context_lang = context.copy()	 	if partner_id:	 		partner_lang = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context).lang	 		context_lang.update({'lang': partner_lang})	 	return self.pool.get('res.users').browse(cr, uid, uid, context=context_lang).company_id.sale_note	def _get_default_company(self, cr, uid, context=None):	 	company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)	 	#if not company_id:	 	#raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))	 	return company_id	def onchange_delivery_id(self, cr, uid, ids, company_id, partner_id, delivery_id, fiscal_position, context=None):		r = {'value': {}}		if not fiscal_position:			if not company_id:				company_id = self._get_default_company(cr, uid, context=context)			fiscal_position = self.pool['account.fiscal.position'].get_fiscal_position(cr, uid, company_id, partner_id,																					   delivery_id, context=context)			if fiscal_position:				r['value']['fiscal_position'] = fiscal_position		return r	def onchange_partner_id(self, cr, uid, ids, part, partner_id, partner_invoice_id, partner_shipping_id, payment_term,							fiscal_position, company_id, context=None):		if not partner_id:			return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'payment_term': False,							  'fiscal_position': False}}		part = self.pool.get('res.partner').browse(cr, uid, partner_id)		addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])		pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False		payment_term = part.property_payment_term and part.property_payment_term.id or False		dedicated_salesman = part.user_id and part.user_id.id or uid		val = {			'partner_invoice_id': addr['invoice'],			'partner_shipping_id': addr['delivery'],			'payment_term': payment_term,			'user_id': dedicated_salesman,			'account_id': part.property_account_receivable,			'date_invoice': datetime.date.today(),		}		delivery_onchange = self.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,													  context=context)		val.update(delivery_onchange['value'])		if pricelist:			val['pricelist_id'] = pricelist		sale_note = self.get_salenote(cr, uid, ids, part.id, context=context)		if sale_note: val.update({'note': sale_note})		return {'value': val}	@api.multi	def action_cancel(self):		for self in self:			moves = self.env['account.move']			for inv in self:				if inv.move_id:					moves += inv.move_id				if inv.payment_ids:					for move_line in inv.payment_ids:						if move_line.reconcile_partial_id.line_partial_ids:							raise exceptions.Warning(_('Error!'), _(								'You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))			self.mapped('invoice_line.picking_id').write({'invoice_state': '2binvoiced'})			# First, set the invoices as cancelled and detach the move ids			#self.write({'state': 'cancel', 'move_id': False, 'internal_number': ''})			# delete the move this invoice was pointing to			# Note that the corresponding move_lines and move_reconciles			# will be automatically deleted too			if moves:				# second, invalidate the move(s)				moves.button_cancel()			self.env.cr.execute('select order_id from sale_order_invoice_rel  where invoice_id = %s' % (self.id))			sale_ids = self.env.cr.fetchall()			for sale_id in sale_ids:				sale_obj = self.env['sale.order'].browse(sale_id)				for sale_id in sale_obj:					sale_id.write({'state': 'progress','internal_invoice_number':self.internal_number,})					picking = self.env['stock.picking'].search([('origin', '=', sale_id.name)])					sale_id.write({'is_modify':True})					for pick in picking:						picki_obj = self.env['stock.picking'].browse(pick.id)						context = {}						context.update({'active_id': pick.id})						ret = self.pool.get('stock.return.picking').create(self._cr,self._uid,{'invoice_state':'2binvoiced'})						pick.write({'state': 'draft'})						#pick.unlink()						self.pool.get('stock.return.picking').createreturns(self._cr,self._uid, [ret],context)						move_obj = self.env['stock.move'].search([('picking_id', '=', pick.id)])						for move_ids in move_obj:							move_ids.write({'state': 'draft'})			account_move_id = self.env['account.invoice'].search([('id', '=', self.id)]).move_id		super(account_invoice, self).action_cancel()class AccountInvoiceLine(models.Model):	_inherit = 'account.invoice.line'	move = fields.Many2one('stock.move', string='Stock Move')	picking_id = fields.Many2one(		string='Picking', comodel_name='stock.picking',		related='move.picking_id', readonly=True)