# -*- coding: utf-8 -*-##################################################################################                                                                               ##    sale_automatic_workflow for OpenERP                                        ##    Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>   ##    Copyright 2013 Camptocamp SA (Guewen Baconnier)                            ##                                                                               ##    This program is free software: you can redistribute it and/or modify       ##    it under the terms of the GNU Affero General Public License as             ##    published by the Free Software Foundation, either version 3 of the         ##    License, or (at your option) any later version.                            ##                                                                               ##    This program is distributed in the hope that it will be useful,            ##    but WITHOUT ANY WARRANTY; without even the implied warranty of             ##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              ##    GNU Affero General Public License for more details.                        ##                                                                               ##    You should have received a copy of the GNU Affero General Public License   ##    along with this program.  If not, see <http://www.gnu.org/licenses/>.      ##                                                                               ##################################################################################import loggingfrom contextlib import contextmanagerfrom openerp.osv import ormfrom openerp import netsvc, _"""Some comments about the implementationIn order to validate the invoice and the picking, we have to usescheduled actions, because if we directly jump the various steps in theworkflow of the invoice and the picking, the sale order workflow will bebroken.The explanation is 'simple'. Example with the invoice workflow: When weare in the sale order at the workflow router, a transition like a signalor condition will change the step of the workflow to the step 'invoice';this step will launch the creation of the invoice.  If the invoice isdirectly validated and reconciled with the payment, the subworkflow willend and send a signal to the sale order workflow.  The problem is thatthe sale order workflow has not yet finished to apply the step 'invoice',so the signal of the subworkflow will be lost because the step 'invoice'is still not finished. The step invoice should be finished beforereceiving the signal. This means that we can not directly validate everysteps of the workflow in the same transaction.If my explanation is not clear, contact me by email and I will improveit: sebastien.beau@akretion.com"""_logger = logging.getLogger(__name__)@contextmanagerdef commit(cr):	"""	Commit the cursor after the ``yield``, or rollback it if an	exception occurs.	Warning: using this method, the exceptions are logged then discarded.	"""	try:		yield	except Exception:		#cr.rollback()		_logger.exception('Error during an automatic workflow action.')	else:		cr.commit()class automatic_workflow_job(orm.Model):	""" Scheduler that will play automatically the validation of	invoices, pickings...  """	_name = 'automatic.workflow.job'    #def _get_domain_for_sale_validation(self, cr, uid, context=None):        #return [('state', '=', 'draft'),                #('workflow_process_id.validate_order', '=', True)]	def _validate_sale_orders(self, cr, uid, context):		wf_service = netsvc.LocalService("workflow")		sale_obj = self.pool.get('sale.order')		#domain = self._get_domain_for_sale_validation(cr, uid, context=context)		#sale_ids = sale_obj.search(cr, uid, domain, context=context)		sale_ids = sale_obj.search(cr, uid, [('state', 'in', ['manual','invoice_except','draft']),			 ('workflow_process_id.validate_order', '=', True)], context=context)		_logger.debug('Sale Orders to validate: %s', sale_ids)		picking_obj = self.pool.get('stock.picking')		for sale_id in sale_ids:			#with commit(cr):			wf_service.trg_validate(uid, 'sale.order',									sale_id, 'order_confirm', cr)			sale = sale_obj.browse(cr, uid,sale_id, context=context)			pick_ids = picking_obj.search(cr, uid, [('origin','=',sale.name)], context=context)			#pick_ids.write({'state': 'assigned'})			#picking_obj.write(cr, uid, pick_ids,{'workflow_process_id': sale.workflow_process_id.id})			picking_obj.write(cr, uid, invoice_id,{'immediate': True,													'payment_term': sale.payment_term.id,													'partner_shipping_id' : sale.partner_shipping_id.id,													'carriage_condition_id' : sale.carriage_condition_id.id,													'goods_description_id' : sale.goods_description_id.id,													'transportation_reason_id' : sale.transportation_reason_id.id,													'transportation_method_id' : sale.transportation_method_id.id,													'carrier_id' : order.carrier_id.id,													'dataora' : order.dataora,													'workflow_process_id': sale.workflow_process_id.id})			sale.write({'state': 'done'})	def _reconcile_invoices(self, cr, uid, ids=None, context=None):		invoice_obj = self.pool.get('account.invoice')		if ids is None:			ids = invoice_obj.search(cr, uid,									 [('state', 'in', ['open'])],									 context=context)		for invoice_id in ids:			with commit(cr):				invoice_obj.reconcile_invoice(cr, uid,											  [invoice_id],											  context=context)	def _validate_invoices(self, cr, uid, pick_id, context):		#pick_id = context.get('active_id', False)		#print context		print 'pick_id', pick_id		wf_service = netsvc.LocalService("workflow")		invoice_obj = self.pool.get('account.invoice')		# invoice_ids = invoice_obj.search(		# 	cr, uid,		# 	[('state', 'in', ['draft','cancel']),		# 	 ('workflow_process_id.validate_invoice', '=', True)],		# 	context=context)		invoice = cr.execute('select invoice_id from sale_order_invoice_rel where order_id = %s' , (pick_id,))		print invoice		if invoice :			invoice_id = cr.fetchone()[0]			print 'invoice_id', invoice_id			_logger.debug('Invoices to validate: %s', invoice_id)			picking_obj = self.pool.get('stock.picking')			order_obj = self.pool.get('sale.order')			#for invoice_id in invoice_ids:			#with commit(cr):			wf_service.trg_validate(uid, 'account.invoice',	invoice_id, 'invoice_open', cr)			invoice = invoice_obj.browse(cr, uid,invoice_id, context=context)			order_ids = order_obj.search(cr, uid, [('id','=',pick_id)], context=context)			order = order_obj.browse(cr, uid,order_ids, context=context)			#order_obj.write(cr, uid, order_ids[0],{'state': 'done'})			#pick_ids = picking_obj.search(cr, uid, [('origin','=',invoice.origin)], context=context)			#picking_obj.write(cr, uid, pick_ids[0],{'invoice_state':'invoiced'})			invoice_obj.write(cr, uid, invoice_id,{'immediate': True,												   'payment_term': order.payment_term.id or False,												   'partner_shipping_id' : order.partner_shipping_id.id or False,												   'carriage_condition_id' : order.carriage_condition_id.id or False,												   'goods_description_id' : order.goods_description_id.id or False,												   'transportation_reason_id' : order.transportation_reason_id.id or False,												   'transportation_method_id' : order.transportation_method_id.id or False,												   'carrier_id' : order.carrier_id.id or False,												   'dataora' : order.dataora,												   'internal_invoice_number' : order.internal_invoice_number or False												   })		else:			invoice_id = self.pool.get('sale.order')._make_invoice(cr, uid,pick_id,[], context=context)			# for record in self.pool.get('sale.order').browse(cr, uid, pick_id, context=context):			# 	print record.name			# 	invoice_id = invoice_obj.create(cr,uid, {	'name':record.name,			# 												'date_invoice':record.date_order,			# 												'partner_id': record.partner_id.id,			# 												'account_id': 33,			# 												'immediate': True,			# 												'payment_term': record.payment_term.id or False,			# 												'partner_shipping_id' : record.partner_shipping_id.id or False,			# 												'carriage_condition_id' : record.carriage_condition_id.id or False,			# 												'goods_description_id' : record.goods_description_id.id or False,			# 												'transportation_reason_id' : record.transportation_reason_id.id or False,			# 												'transportation_method_id' : record.transportation_method_id.id or False,			# 												'carrier_id' : record.carrier_id.id or False,			# 												'dataora' : record.dataora,			# 												'internal_invoice_number' : record.internal_invoice_number or False			# 										 })			# 	for line in record.order_line:			# 		invoice_obj.write(cr, uid, invoice_id, {'immediate': True,			# 										   'payment_term': line.payment_term.id or False,			# 										   'partner_shipping_id' : line.partner_shipping_id.id or False,			# 										   'carriage_condition_id' : line.carriage_condition_id.id or False,			# 										   'goods_description_id' : line.goods_description_id.id or False,			# 										   'transportation_reason_id' : line.transportation_reason_id.id or False,			# 										   'transportation_method_id' : line.transportation_method_id.id or False,			# 										   'carrier_id' : line.carrier_id.id or False,			# 										   'dataora' : line.dataora,			# 										   'internal_invoice_number' : line.internal_invoice_number or False			# 										   })			invoice_obj.signal_workflow(cr,uid,invoice_id,'invoice_open',context)			#mod_obj = self.pool.get('ir.model.data')			#view_ref = mod_obj.get_object_reference(cr, uid,'account', 'invoice_form')			#view_id = view_ref[1] if view_ref else False			#res = {				  #'name':  _('Customer Invoice'),				  #'view_type': 'form',				  #'view_mode': 'form',				  #'view_id': view_ref[1] if view_ref else False,				  #'res_model': 'account.invoice',				  #'context': "{}",				  #'type': 'ir.actions.act_window',				  #'nodestroy': True,				  #'target': 'current',				  #'res_id': invoice_id or False,}##please replace record_id and provide the id of the record to be opened			#return res	def _validate_pickings(self, cr, uid, context):		picking_obj = self.pool.get('stock.picking')		picking_out_obj = self.pool.get('stock.picking')		move_obj = self.pool.get('stock.move')		# We search on stock.picking (using the type) rather than		# stock.picking.out because the ORM seems bugged and can't		# search on stock_picking_out.workflow_process_id.		# Later, we'll call `validate_picking` on stock.picking.out		# because anyway they have the same ID and the call will be at		# the correct object level.		picking_ids = picking_obj.search(			cr, uid,			[('state', 'in', ['draft', 'confirmed', 'assigned']),			 ('workflow_process_id.validate_picking', '=', True)],			context=context)		_logger.debug('Pickings to validate: %s', picking_ids)		move_ids = move_obj.search(cr, uid,[('picking_id', 'in', picking_ids)], context=context)		_logger.debug('Move to validate: %s', move_ids)		if picking_ids:			with commit(cr):				picking_out_obj.validate_picking(cr, uid,												 picking_ids,												 context=context)				move_obj.write(cr, uid, move_ids,{'state':'confirmed'})				picking_out_obj.force_assign(cr, uid,												 picking_ids,												 context=context)				### chiude il movimento ###				move_obj.action_done(cr, uid, move_ids, context=context)				picking_out_obj.write(cr, uid, picking_ids,{'invoice_state':'2binvoiced'})				picking_out_obj.write(cr, uid, picking_ids,{'partner_shipping_id' : self.partner_shipping_id.id,											'payment_term': self.payment_term.id,											'carriage_condition_id' : self.carriage_condition_id.id,											'goods_description_id' : self.goods_description_id.id,											'transportation_reason_id' : self.transportation_reason_id.id,											'transportation_method_id' : self.transportation_method_id.id,											'carrier_id' : self.carrier_id.id,											'dataora' : self.dataora,											'workflow_process_id': self.workflow_process_id.id})				### attesa riscontro magazziniere ###				#picking_out_obj.write(cr, uid, picking_ids,{'invoice_state':'invoiced','state':'confirmed'})	def run(self, cr, uid, ids=None, context=None):		""" Must be called from ir.cron """		self._validate_sale_orders(cr, uid, context=context)		self._validate_invoices(cr, uid, context=context)		self._reconcile_invoices(cr, uid, context=context)		self._validate_pickings(cr, uid, context=context)		return True