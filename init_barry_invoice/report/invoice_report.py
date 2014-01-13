# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################
import time
from openerp import pooler
from openerp.report import report_sxw

class account_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_invoice, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_total_amount_partner': self.get_total_amount_partner,
            'get_balance_due': self.get_balance_due,
            'check_discount': self.check_discount
        })
        
    def get_total_amount_partner(self, partner_id, invoice_line):
        total_amount = 0
        invoice_ids = self.pool.get('account.invoice').search(self.cr, self.uid,[('partner_id', '=', partner_id)])    
        invoice_line_obj = pooler.get_pool(self.cr.dbname).get('account.invoice.line')
        for id in invoice_ids:
            price_subtotal = invoice_line_obj.read(self.cr, self.uid, id)
            total_amount += price_subtotal['price_subtotal']
        total_amount += invoice_line.price_subtotal
        return total_amount
    
    def get_balance_due(self, partner_id):
        total_amount = 0
#        invoice_ids = self.pool.get('account.invoice').search(self.cr, self.uid,[('partner_id', '=', partner_id),('residual','>', 0)])    
#        
#        for inv_obj in self.pool.get('account.invoice').browse(self.cr, self.uid, invoice_ids):
#            total_amount += inv_obj.residual
        invoice_ids = self.pool.get('account.invoice').search(self.cr, 1 ,[('partner_id', '=', partner_id),('state','=', 'open')])    
        
        for inv_obj in self.pool.get('account.invoice').browse(self.cr, 1, invoice_ids):
            total_amount += inv_obj.amount_untaxed
        return total_amount
    
    def check_discount(self, invoice_id):
        flag = False
        invoice_line_obj = self.pool.get('account.invoice.line')
        for l in invoice_id.invoice_line:
            if l.discount > 0.0:
                flag = True
                break                
        return flag
    
from openerp.netsvc import Service
del Service._services['report.account.invoice']
    
report_sxw.report_sxw(
    'report.account.invoice',
    'account.invoice',
    'addons/init_barry_invoice/report/account_print_invoice.rml',
    parser=account_invoice
)