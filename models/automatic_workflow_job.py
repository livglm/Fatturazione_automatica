# -*- coding: utf-8 -*-############################################################################### For copyright and license notices, see __openerp__.py file in root directory##############################################################################import loggingfrom contextlib import contextmanagerfrom openerp.osv import ormfrom openerp import netsvc, _, workflow_logger = logging.getLogger(__name__)@contextmanagerdef commit(cr):	"""	Commit the cursor after the ``yield``, or rollback it if an	exception occurs.	Warning: using this method, the exceptions are logged then discarded.	"""	try:		yield	except Exception:		#cr.rollback()		_logger.exception('Error during an automatic workflow action.')	else:		cr.commit()class automatic_workflow_job(orm.Model):	""" Scheduler that will play automatically the validation of	invoices, pickings...  """	_name = 'automatic.workflow.job'	def _reconcile_invoices(self, cr, uid, ids=None, context=None):		invoice_obj = self.pool.get('account.invoice')		if ids is None:			ids = invoice_obj.search(cr, uid,									 [('state', 'in', ['open'])],									 context=context)		for invoice_id in ids:			with commit(cr):				invoice_obj.reconcile_invoice(cr, uid,											  [invoice_id],											  context=context)	def _validate_invoices(self, cr, uid, pick_id, context):		if self.pool.get('account.invoice').search(cr,uid,[('origin','=',pick_id.name)]):			invoice_id = self.pool.get('account.invoice').search(cr,uid,[('origin','=',pick_id.name)])[0]			if invoice_id :				invoice_obj = self.pool.get('account.invoice')				_logger.debug('Invoices to validate: %s', invoice_id)				picking_obj = self.pool.get('stock.picking')				order_obj = self.pool.get('sale.order')				workflow.trg_validate(uid, 'account.invoice',	invoice_id, 'invoice_open', cr)				invoice = invoice_obj.browse(cr, uid,invoice_id, context=context)				order_ids = order_obj.search(cr, uid, [('id','=',pick_id.id)], context=context)				order = order_obj.browse(cr, uid,order_ids, context=context)				invoice_obj.write(cr, uid, invoice_id,{'immediate': True,													   'payment_term': order.payment_term.id or False,													   'partner_shipping_id' : order.partner_shipping_id.id or False,													   'carriage_condition_id' : order.carriage_condition_id.id or False,													   'goods_description_id' : order.goods_description_id.id or False,													   'transportation_reason_id' : order.transportation_reason_id.id or False,													   'transportation_method_id' : order.transportation_method_id.id or False,													   'carrier_id' : order.carrier_id.id or False,													   'dataora' : order.dataora,													   'internal_invoice_number' : order.internal_invoice_number or False													   })				invoice_obj.button_reset_taxes(cr,uid,invoice_id)