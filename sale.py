# -*- coding: utf-8 -*-##################################################################################                                                                               ##                                                                               ##    This program is free software: you can redistribute it and/or modify       ##    it under the terms of the GNU Affero General Public License as             ##    published by the Free Software Foundation, either version 3 of the         ##    License, or (at your option) any later version.                            ##                                                                               ##    This program is distributed in the hope that it will be useful,            ##    but WITHOUT ANY WARRANTY; without even the implied warranty of             ##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              ##    GNU Affero General Public License for more details.                        ##                                                                               ##    You should have received a copy of the GNU Affero General Public License   ##    along with this program.  If not, see <http://www.gnu.org/licenses/>.      ##                                                                               ##################################################################################from openerp import models, fields, api, netsvc, _, workflow, exceptionsimport timeimport pdbclass res_partner_sale(models.Model):	_inherit = "res.partner"	is_carrier = fields.Boolean('Trasportatore')class sale_order(models.Model):	_inherit = "sale.order"	workflow_process_id = fields.Many2one('sale.workflow.process','Sale Workflow Process')	payment_term = fields.Many2one('account.payment.term', 'Payment Term')	partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',  required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current sales order.")	partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',  required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current sales order.")	fiscal_position = fields.Many2one('account.fiscal.position', 'Fiscal Position')	delivery_address_id = fields.Many2one('res.partner', string='Delivery Address', required=False)	carriage_condition_id = fields.Many2one('stock.incoterms', 'Incoterms')	goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of Goods')	transportation_reason_id = fields.Many2one('stock.picking.transportation_reason','Reason for Transportation')	transportation_method_id = fields.Many2one('stock.picking.transportation_method','Method of Transportation')	carrier_id = fields.Many2one('delivery.carrier', string='Carrier')	invoce_id = fields.Many2one('account.invoice')	dataora = fields.Datetime('Data e ora trasporto')	internal_invoice_number = fields.Char('Numero Fattura')	@api.multi	def action_cancel(self):		super(sale_order, self).action_cancel()		for sale in self.browse():			for inv in sale.invoice_ids:				inv.write({'state' :'draft'})				inv.unlink()		location_id = self.env['stock.location'].search([('usage','=','customer')])		#move_obj = self.env['stock.move'].search([('origin','=',self.name),('location_id','in',[location_id.id])])		move_obj = self.env['stock.move'].search([('origin','=',self.name)])		for move_ids in move_obj:			for quant in self.env['stock.quant'].search([('negative_move_id','=',move_ids.id)]):				for quant_item in quant.search([('propagated_from_id','=',quant.id)]):					quant.unlink()					quant_item.unlink()			move_ids.write({'state': 'draft'})			move_ids.unlink()		for sale_id in self:			sale_id.write({'state': 'progress','procurement_group_id':''})		for line in self.env['sale.order.line'].search([('order_id','=',self.id)]):			line.write({'state': 'draft'})			for proc_order in self.env['procurement.order'].search([('sale_line_id','=',line.id)]):				proc_order.write({'state': 'cancel'})				proc_order.unlink()		quant_obj = self.pool.get("stock.quant")		pick = self.env['stock.picking'].search([('origin','=',self.name)])		for picking in pick:			pack_obj = self.env['stock.pack.operation'].search([('picking_id','=',picking.id)])			for pack in pack_obj:				pack.unlink()			#picking.write({'state': 'done'})			picking.unlink()			#picking.ensure_one()		self.write({'state': 'draft'})		#super(sale_order, self).action_cancel()	def _prepare_invoice(self, cr, uid, order, lines, context=None):		invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)		workflow = order.workflow_process_id		if not workflow:			return invoice_vals		invoice_vals['workflow_process_id'] = workflow.id		if workflow.invoice_date_is_order_date:			invoice_vals['date_invoice'] = order.date_order		return invoice_vals	def _prepare_order_picking(self, cr, uid, order, context=None):		picking_vals = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)		if order.workflow_process_id:			picking_vals['workflow_process_id'] = order.workflow_process_id.id		return picking_vals	def onchange_payment_method_id(self, cr, uid, ids, payment_method_id, context=None):		values = super(sale_order, self).onchange_payment_method_id(cr, uid, ids, payment_method_id, context=context)		if not payment_method_id:			return values		method_obj = self.pool.get('payment.method')		method = method_obj.browse(cr, uid, payment_method_id, context=context)		workflow = method.workflow_process_id		if workflow:			values.setdefault('value', {})			values['value']['workflow_process_id'] = workflow.id		return values	def onchange_workflow_process_id(self, cr, uid, ids, workflow_process_id, context=None):		if not workflow_process_id:			return {}		result = {}		workflow_obj = self.pool.get('sale.workflow.process')		workflow = workflow_obj.browse(cr, uid, workflow_process_id, context=context)		if workflow.picking_policy:			result['picking_policy'] = workflow.picking_policy		if workflow.order_policy:			result['order_policy'] = workflow.order_policy		if workflow.invoice_quantity:			result['invoice_quantity'] = workflow.invoice_quantity		return {'value': result}	def test_create_invoice(self, cr, uid, ids):		""" Workflow condition: test if an invoice should be created,		based on the automatic workflow rules """		if isinstance(ids, (list, tuple)):			assert len(ids) == 1			ids = ids[0]		order = self.browse(cr, uid, ids)		if order.order_policy != 'manual' or not order.workflow_process_id:			return False		invoice_on = order.workflow_process_id.create_invoice_on		if invoice_on == 'on_order_confirm':			return True		elif invoice_on == 'on_picking_done' and order.shipped:			return True		return False	@api.multi	def action_button_confirm(self):		picking_vals = super(sale_order, self).action_button_confirm()		picking = self.env['stock.picking']		if self.workflow_process_id.id:			work = self.env['automatic.workflow.job'] #.with_context({'active_id':self.id })			sale_workflow = self.env['sale.workflow.process'].search([('id','=',self.workflow_process_id.id)])			for workflows in sale_workflow:				if workflows.validate_order:					#work._validate_sale_orders(context=self.id)					#wf_service = netsvc.LocalService("workflow")					sale_obj = self.pool.get('sale.order')					picking_obj = self.env['stock.picking']					workflow.trg_validate(self._uid, 'sale.order',											self.id, 'order_confirm', self._cr)					pick_ids = picking_obj.search([('origin','=',self.name)])					pick_ids.write({'state': 'cancel'})					#pick_ids.write({'workflow_process_id': self.workflow_process_id.id})					for line in self.env['sale.order.line'].search([('order_id','=',self.id)]):						line.write({'state': 'draft'})					#self.write({'state': 'manual'})					#_logger.debug('Sale Orders to validate: %s', self.id)					self.action_ship_create()					for line in self.env['sale.order.line'].search([('order_id','=',self.id)]):						line.write({'state': 'done'})					picking_out_obj = self.env['stock.picking'].search([('origin', '=', self.name)])					picking_out_obj.write({'partner_shipping_id' : self.partner_shipping_id.id or False,												'partner_invoice_id' : self.partner_invoice_id.id or False,												'payment_term': self.payment_term.id or False,												'carriage_condition_id' : self.carriage_condition_id.id or False,												'goods_description_id' : self.goods_description_id.id or False,												'transportation_reason_id' : self.transportation_reason_id.id or False,												'transportation_method_id' : self.transportation_method_id.id or False,												'carrier_id' : self.carrier_id.id or False,												'dataora' : self.dataora or False,												'workflow_process_id': self.workflow_process_id.id or False,												'fiscal_position' : self.fiscal_position.id or False})				if workflows.validate_picking:					#self.write({'state': 'manual'})					#picking_obj = self.env['stock.picking']					#picking_out_obj = self.env['stock.picking']					#move_obj = self.env['stock.move']					#picking_ids = picking_obj.search([('origin', '=', self.name), ('state','=','draft')])					##for picking_out_obj in picking_ids					#if picking_ids:						#picking_ids._validate_pickings()						##picking_out_obj.validate_picking(picking_ids.id)						##move_ids = move_obj.search([('picking_id', 'in', picking_ids.id)], context=context)						#move_ids = move_obj.search([('picking_id', '=', picking_ids.id)])						#move_ids.write({'state':'confirmed'})						##picking_out_obj.force_assign(picking_ids)						#picking_ids.force_assign()						#picking_out_obj = self.pool.get('stock.picking')						#### chiude il movimento ###						##move_obj.action_done(move_ids)						#move_ids.action_done()						#picking_out_obj.write({'invoice_state':'2binvoiced'})						#### attesa riscontro magazziniere ###						##picking_out_obj.write(cr, uid, picking_ids,{'invoice_state':'invoiced','state':'confirmed'})					picking_obj = self.pool.get('stock.picking')					move_obj = self.pool.get('stock.move')					picking_ids = picking_obj.search(self._cr, self._uid,[('id', '=',  picking_out_obj.id)])					move_ids = move_obj.search(self._cr, self._uid, [('picking_id', '=', picking_out_obj.id)])					if picking_ids:						# picking_out_obj.validate_picking(cr, uid, picking_ids, context=context)						move_obj.write(self._cr, self._uid, move_ids, {'state': 'confirmed'})						picking_obj.force_assign(self._cr, self._uid, picking_ids)						### chiude il movimento ###						move_obj.action_done(self._cr, self._uid, move_ids)						picking_obj.write(self._cr, self._uid, picking_ids, {'invoice_state': '2binvoiced'})				self.update_invoice()				if workflows.validate_invoice:					work._validate_invoices(self)					work._reconcile_invoices()				if workflows.validate_invoice:					invoice_obj = self.env['account.invoice']					invoice_id = invoice_obj.search([('origin','=',self.name)])					view_ref = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')					view_id = view_ref[1] if view_ref else False					res = {						'name':  _('Customer Invoice'),						'view_type': 'form',						'view_mode': 'form',						'view_id': view_ref[1] if view_ref else False,						'res_model': 'account.invoice',						'context': "{}",						'type': 'ir.actions.act_window',						'nodestroy': True,						'target': 'current',						'res_id': invoice_id.id  or False,##please replace record_id and provide the id of the record to be opened					}					return res		#self.write({'state': 'manual'})	@api.multi	def update_invoice(self):		#order = self.browse()[0]		#print "order",order		invoice_id_list = []		invoice_id_list2 = []		invoice_line_obj = self.env['account.invoice.line']		account_id = self.env['ir.property'].get( 'property_account_expense_categ', 'product.category').id		picking_id = self.env['stock.picking'].search( [('origin', '=', self.name)])		for picking in picking_id:			#if self.env['stock.picking'].browse(picking).state == 'assigned':			if picking.state == 'assigned':				picking_record = picking		self.env.cr.execute('select invoice_id from sale_order_invoice_rel  where order_id = %s' % (self.id))		invoice_id = self.env.cr.fetchone()[0]		#invoice_id = self.get_invoice_id(self.id)		invoice_record = self.env['account.invoice'].browse( invoice_id)		for invoice in self.invoice_ids:			invoice_id_list2.append(invoice.invoice_line)		for order_line in self.order_line:			#pdb.set_trace()			if order_line.invoice_lines:				for invoice in order_line.invoice_lines:					invoice_id_list.append(invoice.id)			print invoice_id_list,invoice_id_list2			move_ids = self.env['stock.move'].search([('origin','=',self.name)])[0]			if move_ids:				move_state = move_ids.state			if self.order_policy != 'picking':				res = self.env['sale.order.line']._prepare_order_line_invoice_line(order_line)				print res				if move_ids:					for invoice_line_id in order_line.invoice_lines:						#if move_state != 'done':						#print invoice_line_id						invoice_line_id.write(res)				else:					res['invoice_id'] = invoice_id					inv_id = invoice_line_obj.create( res)					self.env['sale.order.line'].write([order_line.id], {'invoice_lines': [(4, inv_id)]})			else:				if order_line.move_ids:					for invoice_line_id in order_line.invoice_lines:						if invoice_line_id.invoice_id.state == 'draft':							invoice_line_obj.write( invoice_line_id.id, {'price_unit': order_line.price_unit})		if self.order_policy != 'picking':			for invoice_list in invoice_id_list2:				for invoice in invoice_list:					if not invoice.id in invoice_id_list:						invoice_line_obj.unlink()		#return True	def action_update_order_line(self, cr, uid, ids, context=None):		if context is None:			context = {}		self.update_invoice(cr, uid, ids, context)		self.update_moves(cr, uid, ids, context)		self.write(cr, uid, ids, {'is_modify': False}, context=context)		return True	def has_valuation_moves(self):		self.ensure_one()		account_moves = self.env['account.move'].search(			[('ref', '=', self.name)])		return bool(account_moves)	@api.multi	def action_revert_done(self):		for picking in self:			if picking.has_valuation_moves():				raise exceptions.Warning(					_('Picking %s has valuation moves: '						'remove them first.')					% (picking.name))			if picking.invoice_id:				raise exceptions.Warning(					_('Picking %s has invoices!') % (picking.name))			picking.move_lines.write({'state': 'draft'})			picking.state = 'draft'			if picking.invoice_state == 'invoiced' and not picking.invoice_id:				picking.invoice_state = '2binvoiced'			# Deleting the existing instance of workflow			workflow.trg_delete(				self._uid, 'stock.picking', picking.id, self._cr)			workflow.trg_create(				self._uid, 'stock.picking', picking.id, self._cr)			picking.message_post(				_("The picking has been re-opened and set to draft state"))		return	def action_ship_create(self, cr, uid, ids, context=None):		"""Create the required procurements to supply sales order lines, also connecting		the procurements to appropriate stock moves in order to bring the goods to the		sales order's requested location.		:return: True		"""		context = context or {}		#context['lang'] = self.pool['res.users'].browse(cr, uid, uid).lang		procurement_obj = self.pool.get('procurement.order')		sale_line_obj = self.pool.get('sale.order.line')		order_obj = self.browse(cr, uid, ids, context=context)		for order in order_obj: #self.browse(cr, uid, ids, context=context):			proc_ids = []			vals = self._prepare_procurement_group(cr, uid, order, context=context)			if not order.procurement_group_id:				group_id = self.pool.get("procurement.group").create(cr, uid, vals, context=context)				order.write({'procurement_group_id': group_id})			for line in order.order_line:				if line.state == 'cancel':					continue				#Try to fix exception procurement (possible when after a shipping exception the user choose to recreate)				if line.procurement_ids:					#first check them to see if they are in exception or not (one of the related moves is cancelled)					procurement_obj.check(cr, uid, [x.id for x in line.procurement_ids if x.state not in ['cancel', 'done']])					line.refresh()					#run again procurement that are in exception in order to trigger another move					except_proc_ids = [x.id for x in line.procurement_ids if x.state in ('exception', 'cancel')]					procurement_obj.reset_to_confirmed(cr, uid, except_proc_ids, context=context)					proc_ids += except_proc_ids				elif sale_line_obj.need_procurement(cr, uid, [line.id], context=context):					if (line.state == 'done') or not line.product_id:						continue					vals = self._prepare_order_line_procurement(cr, uid, order, line, group_id=order.procurement_group_id.id, context=context)					ctx = context.copy()					ctx['procurement_autorun_defer'] = True					proc_id = procurement_obj.create(cr, uid, vals, context=ctx)					proc_ids.append(proc_id)			#Confirm procurement order such that rules will be applied on it			#note that the workflow normally ensure proc_ids isn't an empty list			procurement_obj.run(cr, uid, proc_ids, context=context)			#if shipping was in exception and the user choose to recreate the delivery order, write the new status of SO			if order.state == 'shipping_except':				val = {'state': 'progress', 'shipped': False}				if (order.order_policy == 'manual'):					for line in order.order_line:						if (not line.invoiced) and (line.state not in ('cancel', 'draft')):							val['state'] = 'manual'							break				order.write(val)		return True	def _prepare_invoice(self, cr, uid, order, lines, context=None):		"""Prepare the dict of values to create the new invoice for a		   sales order. This method may be overridden to implement custom		   invoice generation (making sure to call super() to establish		   a clean extension chain).		   :param browse_record order: sale.order record to invoice		   :param list(int) line: list of invoice line IDs that must be								  attached to the invoice		   :return: dict of value to create() the invoice		"""		if context is None:			context = {}		journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']		if not journal_id:			raise exceptions.Warning(_('Error!'),				_('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))		invoice_vals = {			'name': order.client_order_ref or '',			'origin': order.name,			'type': 'out_invoice',			'reference': order.client_order_ref or order.name,			'account_id': order.partner_invoice_id.property_account_receivable.id,			'partner_id': order.partner_invoice_id.id,			'journal_id': journal_id,			'invoice_line': [(6, 0, lines)],			'currency_id': order.pricelist_id.currency_id.id,			'comment': order.note,			'payment_term': order.payment_term and order.payment_term.id or False,			'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,			'date_invoice': context.get('date_invoice', False),			'company_id': order.company_id.id,			'user_id': order.user_id and order.user_id.id or False,			'section_id' : order.section_id.id,			'partner_shipping_id' : order.partner_shipping_id.id or False,			'partner_invoice_id' : order.partner_invoice_id.id or False,			'carriage_condition_id' : order.carriage_condition_id.id or False,			'goods_description_id' : order.goods_description_id.id or False,			'transportation_reason_id' : order.transportation_reason_id.id or False,			'transportation_method_id' : order.transportation_method_id.id or False,			'carrier_id' : order.carrier_id.id or False,			'dataora' : order.dataora or False,			'workflow_process_id': order.workflow_process_id.id or False,			}		invoice_vals.update(self._inv_get(cr, uid, order, context=context))		return invoice_valsclass sale_order_line_(models.Model):	_inherit = "sale.order.line"	def button_cancel(self, cr, uid, ids, context=None):		lines = self.browse(cr, uid, ids, context=context)		for procurement in lines.mapped('procurement_ids'):			for move in procurement.move_ids:				if move.state == 'done' and not move.scrapped and not move.origin_returned_move_id:					raise exceptions.Warning(_('Invalid Action!'), _('You cannot cancel a sale order line which is linked to a stock move already done.'))		#return super(sale_order_line_, self).button_cancel(cr, uid, ids, context=context)