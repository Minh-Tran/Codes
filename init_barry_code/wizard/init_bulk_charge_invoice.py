# -*- coding: utf-8 -*-
##############################################################################
#
#    INIT TECH, Open Source Management Solution
#    Copyright (C) 2012-2013 Tiny SPRL (<http://init.vn>).
#
##############################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc

class init_bulk_charge_make_invoice(osv.osv_memory):
    _name = "init.bulk.charge.make.invoice"
    
    _columns = {
    'company_id': fields.many2one('res.company','Company'),
    'account_id': fields.many2one('account.account','Receivable Account', required=True, 
								domain="[('type', '=', 'receivable'),('company_id','=', company_id)]",),    
    }
    _defaults = {
        'company_id': lambda self, cr, uid, c: c.get('company_id', False) or self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    
    def make_invoices(self, cr, uid, ids, context={}):
        bulk_obj = self.pool.get('init.probility.charge')
        account_id = self.browse(cr, uid, ids[0]).account_id.id
        bulk_ids = context.get('bulk_ids', False)
        if not bulk_ids:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created !'))
        bulk_obj.write(cr, uid, bulk_ids, {'property_account_receivable': account_id})
        
        return bulk_obj.action_invoice_create(cr, uid, bulk_ids, dict(context,open_invoice = True))
   

init_bulk_charge_make_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
