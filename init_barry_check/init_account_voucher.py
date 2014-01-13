## -*- coding: utf-8 -*-
###############################################################################
##
##    OpenERP, Open Source Management Solution
##    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU Affero General Public License as
##    published by the Free Software Foundation, either version 3 of the
##    License, or (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU Affero General Public License for more details.
##
##    You should have received a copy of the GNU Affero General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################
from openerp.osv import osv,fields
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler


class account_voucher(osv.osv):

    _inherit = 'account.voucher'
    _columns = {
        'bank_id': fields.many2one('res.partner.bank', 'Bank', domain="[('partner_id','=',partner_id)]"),
        'journal_type': fields.related('journal_id', 'type', type='char', string='Type'),
        'allow_check_writing': fields.related('journal_id', 'allow_check_writing', type='boolean', string='Check'),  
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, 
                                     states={'draft':[('readonly',False)]}, domain="[('company_id','=', company_id)]"),
    }
    
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        vals = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context)
        if journal_id:
            journal_obj = self.pool.get('account.journal').browse(cr, uid, journal_id)
            vals['value'].update({'journal_type': journal_obj.type,
                                  'allow_check_writing': journal_obj.allow_check_writing})
        return vals

#    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_voucher, self).default_get(cr, uid, fields, context=context)
        
        record_ids = context and context.get('active_ids', []) or []
        invoice_obj = self.pool.get('account.invoice')
        company_id = False
        partner_id = False
        if 0 in record_ids:
            record_ids = record_ids.remove(0)
        if record_ids:
            inv_obj = invoice_obj.browse(cr, uid, record_ids[0])
            partner_id = inv_obj.partner_id.id
            
            inv_other_ids = invoice_obj.search(cr, uid, [('id', 'in', record_ids), ('partner_id','!=', inv_obj.partner_id.id)])
            if inv_other_ids:
                raise osv.except_osv('Error!', 'Please choose invoice of supplier: "%s".' % (inv_obj.partner_id.name))
            
            inv_other_ids = invoice_obj.search(cr, uid, [('id', 'in', record_ids), ('company_id','!=', inv_obj.company_id.id)])
            if inv_other_ids:
                raise osv.except_osv('Error!', 'Please choose invoice of company: "%s".' % (inv_obj.company_id.name))
            company_id = inv_obj.company_id.id
                        
        total = 0
        for inv in invoice_obj.browse(cr, uid, record_ids, context=context):
            total += inv.amount_total
            
        journal_pool = self.pool.get('account.journal')
        journal_ids = journal_pool.search(cr, uid, [('allow_check_writing', '=', True)], limit=1)
          
        if 'amount' in fields:
            res['amount'] = total
        if 'company_id' in fields:
            res['company_id'] = company_id
        if 'partner_id' in fields:
            res['partner_id'] = partner_id
#        if 'type' in fields and record_ids:
#            res['type'] = 'payment'
        if 'journal_id' in fields and journal_ids:
            res['journal_id'] = journal_ids[0]
        
                   
        return res
    
account_voucher()