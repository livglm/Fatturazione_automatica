# -*- coding: utf-8 -*-############################################################################### For copyright and license notices, see __openerp__.py file in root directory##############################################################################from openerp import models, fields, api, workflow, _, exceptionsclass stock_picking(models.Model):    _inherit = "stock.picking"    workflow_process_id = fields.Many2one('sale.workflow.process', 'Sale Workflow Process')    payment_term = fields.Many2one('account.payment.term', 'Payment Term')    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},                                         help="Invoice address for current sales order.")    # partner_invoice_id = fields.One2many(related = 'partner_invoice_id.id', relation ='sale.order')    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},                                          help="Delivery address for current sales order.")    fiscal_position = fields.Many2one('account.fiscal.position', 'Fiscal Position')    delivery_address_id = fields.Many2one('res.partner', string='Delivery Address')    carriage_condition_id = fields.Many2one('stock.incoterms', 'Incoterms')    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of Goods')    transportation_reason_id = fields.Many2one('stock.picking.transportation_reason', 'Reason for Transportation')    transportation_method_id = fields.Many2one('stock.picking.transportation_method', 'Method of Transportation')    carrier_id = fields.Many2one('delivery.carrier', string='Carrier')    invoce_id = fields.Many2one('account.invoice')    dataora = fields.Datetime('Data e ora trasporto')    internal_invoice_number = fields.Char('Numero Fattura')    number_of_packages = fields.Integer('Number of packages')    @api.multi    def onchange_delivery_id(self):        r = {'value': {}}        if not fiscal_position:            if not company_id:                company_id = self._get_default_company()            fiscal_obj = self.env['account.fiscal.position'].search([('company_id', '=', company_id)])            fiscal_position = fiscal_obj.get_fiscal_position()            if fiscal_position:                r['value']['fiscal_position'] = fiscal_position        return r    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):        if context is None:            context = {}        partner, currency_id, company_id = key        if inv_type in ('out_invoice', 'out_refund'):            account_id = partner.property_account_receivable.id            payment_term = partner.property_payment_term.id or False        else:            account_id = partner.property_account_payable.id            payment_term = partner.property_supplier_payment_term.id or False        pick_obj = self.pool.get('stock.picking').browse(cr, uid, move.picking_id.id)        print 'pick_obj.number_of_packages',pick_obj.number_of_packages        return {            'origin': move.picking_id.name,            'date_invoice': context.get('date_inv', False),            'user_id': uid,            'partner_id': partner.id,            'account_id': account_id,            'type': inv_type,            'company_id': company_id,            'currency_id': currency_id,            'journal_id': journal_id,            'partner_shipping_id': pick_obj.partner_shipping_id.id or False,            'partner_invoice_id': pick_obj.partner_invoice_id.id or False,            'payment_term': pick_obj.payment_term.id or False,            'carriage_condition_id': pick_obj.carriage_condition_id.id or False,            'goods_description_id': pick_obj.goods_description_id.id or False,            'transportation_reason_id': pick_obj.transportation_reason_id.id or False,            'transportation_method_id': pick_obj.transportation_method_id.id or False,            'carrier_id': pick_obj.carrier_id.id or False,            'dataora': pick_obj.dataora or False,            'workflow_process_id': pick_obj.workflow_process_id.id or False,            'fiscal_position': pick_obj.fiscal_position.id or False,            'internal_invoice_number': pick_obj.internal_invoice_number,            'number_of_packages': pick_obj.number_of_packages       }    def _prepare_invoice(self, cworkflowr, uid, picking, partner, inv_type, journal_id, context=None):        invoice_vals = super(stock_picking, self)._prepare_invoice(            cr, uid, picking, partner, inv_type, journal_id, context=context)        invoice_vals['workflow_process_id'] = picking.workflow_process_id.id        if picking.workflow_process_id.invoice_date_is_order_date:            invoice_vals['date_invoice'] = picking.sale_id.date_order        return invoice_vals    @api.multi    #def cancel_picking(self):    def action_cancel(self):        move_obj = self.env['stock.move'].search([('picking_id', '=', self.id)])        # wf_service = netsvc.LocalService("workflow")        for moves in move_obj:            #move = self.env['stock.move'].browse(moves.id)            moves.write({'state': 'draft'})        print self.invoice_state        if  self.invoice_state == '2binvoiced':            context = {}            context.update({'active_id': self.id})            ret = self.pool.get('stock.return.picking').create(self._cr, self._uid, {'invoice_state': '2binvoiced'})            self.pool.get('stock.return.picking').createreturns(self._cr, self._uid, [ret], context)             #self.write({'state': 'draft'})        sale_ids = self.env['sale.order'].search([('name', '=', self.origin)])        for sale in sale_ids:             sale.write({'state': 'manual'})             for line in sale.order_line:                 line.write({'state': 'draft'})        super(stock_picking,self).action_cancel()    @api.multi    def validate_picking(self):        work = self.env['automatic.workflow.job']        context = {}        context.update({'active_id': self.id})        #print context        self._validate_pickings(context=context)        return True    def _validate_pickings(self, cr, uid, context):        pick_id = context.get('active_id', False)        picking_obj = self.pool.get('stock.picking')        picking_out_obj = self.pool.get('stock.picking')        move_obj = self.pool.get('stock.move')        # We search on stock.picking (using the type) rather than        # stock.picking.out because the ORM seems bugged and can't        # search on stock_picking_out.workflow_process_id.        # Later, we'll call `validate_picking` on stock.picking.out        # because anyway they have the same ID and the call will be at        # the correct object level.        # picking_ids = picking_obj.search(        #     cr, uid,        #     [('state', 'in', ['draft', 'confirmed', 'assigned']), ('id', '=', pick_id)        #      ],        #     context=context)        picking_ids = picking_obj.search(            cr, uid,            [('id', '=', pick_id)             ],            context=context)        # _logger.debug('Pickings to validate: %s', picking_ids)        move_ids = move_obj.search(cr, uid, [('picking_id', 'in', picking_ids)], context=context)        if picking_ids:            # picking_out_obj.validate_picking(cr, uid, picking_ids, context=context)            move_obj.write(cr, uid, move_ids, {'state': 'confirmed'})            picking_out_obj.force_assign(cr, uid, picking_ids, context=context)            ### chiude il movimento ###            move_obj.action_done(cr, uid, move_ids, context=context)            picking_out_obj.write(cr, uid, picking_ids, {'invoice_state': '2binvoiced'})class Stock_Picking_Carriage_Condition(models.Model):    _name = "stock.picking.carriage_condition"    _description = "Carriage Condition"    name = fields.Char(string='Incoterms', required=True)    note = fields.Text(string='Note')class Stock_Picking_Goods_Description(models.Model):    _name = 'stock.picking.goods_description'    _description = "Description of Goods"    name = fields.Char(string='Description of Goods', required=True)    note = fields.Text(string='Note')class Stock_Picking_Transportation_Reason(models.Model):    _name = 'stock.picking.transportation_reason'    _description = 'Reason for Transportation'    name = fields.Char(string='Reason For Transportation', required=True)    note = fields.Text(string='Note')class Stock_Picking_Transportation_Method(models.Model):    _name = 'stock.picking.transportation_method'    _description = 'Method of Transportation'    name = fields.Char(string='Method of Transportation', required=True)    note = fields.Text(string='Note')class StockMove(models.Model):    _inherit = 'stock.move'    lot_id = fields.Many2one('stock.production.lot', 'Serial Number')    #sale_line_id = fields.Many2one('procurement_id','sale_line_id',relation='sale.order.line', readonly=True, store=True, ondelete='set null')    price = fields.Float('Sale Price',compute='compute_price',store=True, readonly=True)    sale_line_id = fields.Many2one('sale.order.line',related ='procurement_id.sale_line_id', readonly=True, store=True, ondelete='set null')    @api.one    @api.depends('sale_line_id')    def compute_price(self):        for line in self.env['sale_order_line'].search([('id','=',self.sale_line_id)])            self.price = line.price_unit    @api.model    def _get_invoice_line_vals(self, move, partner, inv_type):        result = super(StockMove, self)._get_invoice_line_vals(            move, partner, inv_type)        result['move'] = move.id        return resultclass stock_return_picking(models.TransientModel):    _inherit = 'stock.return.picking'    def createreturns(self, cr, uid, ids, context=None):        if context is None:            context = {}        record_id = context and context.get('active_id', False) or False        move_obj = self.pool.get('stock.move')        pick_obj = self.pool.get('stock.picking')        uom_obj = self.pool.get('product.uom')        pick = pick_obj.browse(cr, uid, record_id, context=context)        data = self.read(cr, uid, ids[0], context=context)        canc = False        if not data['product_return_moves']:            move_ids = move_obj.search(cr, uid, [('origin', '=', pick.origin)], context=context)            # move = move_obj.browse(cr, uid, move_id, context=None)            # data = move_obj.read(cr, uid, record_id, context=None)            data['product_return_moves'] = move_ids            data_obj = self.pool.get('stock.move')            canc = True        else:            data_obj = self.pool.get('stock.return.picking.line')        returned_lines = 0        # Cancel assignment of existing chained assigned moves        moves_to_unreserve = []        for move in pick.move_lines:            to_check_moves = [move.move_dest_id] if move.move_dest_id.id else []            while to_check_moves:                current_move = to_check_moves.pop()                if current_move.state not in ('done', 'cancel') and current_move.reserved_quant_ids:                    moves_to_unreserve.append(current_move.id)                split_move_ids = move_obj.search(cr, uid, [('split_from', '=', current_move.id)], context=context)                if split_move_ids:                    to_check_moves += move_obj.browse(cr, uid, split_move_ids, context=context)        if moves_to_unreserve:            move_obj.do_unreserve(cr, uid, moves_to_unreserve, context=context)            # break the link between moves in order to be able to fix them later if needed            move_obj.write(cr, uid, moves_to_unreserve, {'move_orig_ids': False}, context=context)        # Create new picking for returned products        pick_type_id = pick.picking_type_id.return_picking_type_id and pick.picking_type_id.return_picking_type_id.id or pick.picking_type_id.id        new_picking = pick_obj.copy(cr, uid, pick.id, {            'move_lines': [],            'picking_type_id': pick_type_id,            'state': 'draft',            'origin': pick.name,        }, context=context)        for data_get in data_obj.browse(cr, uid, data['product_return_moves'], context=context):            if canc:                move = data_get            else:                move = data_get.move_id            if not move:                raise exceptions.Warning(_('Warning !'),                                         _("You have manually created product lines, please delete them to proceed"))            if canc:                new_qty = data_get.product_uom_qty            else:                new_qty = data_get.quantity            if new_qty:                # The return of a return should be linked with the original's destination move if it was not cancelled                if not canc:                    if move.origin_returned_move_id.move_dest_id.id and move.origin_returned_move_id.move_dest_id.state != 'cancel':                        move_dest_id = move.origin_returned_move_id.move_dest_id.id                    else:                        move_dest_id = False                else:                    move_dest_id = False                returned_lines += 1                if canc:                    move_obj.copy(cr, uid, move.id, {                        'product_id': data_get.product_id.id,                        'product_uom_qty': new_qty,                        'product_uos_qty': new_qty * move.product_uos_qty / move.product_uom_qty,                        'picking_id': new_picking,                        'state': 'draft',                        'location_id': move.location_dest_id.id,                        'location_dest_id': move.location_id.id,                        'picking_type_id': pick_type_id,                        'warehouse_id': pick.picking_type_id.warehouse_id.id,                        'origin_returned_move_id': move.id,                        'procure_method': 'make_to_stock',                        'restrict_lot_id': data_get.lot_id,                        'move_dest_id': move_dest_id,                    })                else:                    move_obj.copy(cr, uid, move.id, {                        'product_id': data_get.product_id.id,                        'product_uom_qty': new_qty,                        'product_uos_qty': new_qty * move.product_uos_qty / move.product_uom_qty,                        'picking_id': new_picking,                        'state': 'draft',                        'location_id': move.location_dest_id.id,                        'location_dest_id': move.location_id.id,                        'picking_type_id': pick_type_id,                        'warehouse_id': pick.picking_type_id.warehouse_id.id,                        'origin_returned_move_id': move.id,                        'procure_method': 'make_to_stock',                        'restrict_lot_id': data_get.lot_id.id,                        'move_dest_id': move_dest_id,                    })        if not returned_lines:            raise exceptions.Warning(_('Warning!'), _("Please specify at least one non-zero quantity."))        pick_obj.action_confirm(cr, uid, [new_picking], context=context)        pick_obj.force_assign(cr, uid, [new_picking], context)        pick_obj.action_assign(cr, uid, [new_picking], context)        pick_obj.do_transfer(cr, uid, [new_picking], context)        return new_picking, pick_type_id