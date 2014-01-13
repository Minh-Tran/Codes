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
#
#from openerp.osv import osv
#from openerp.tools.translate import _
#from openerp import netsvc
#from openerp import pooler
#
#class wizard_create_check(osv.osv_memory):
#
#    _name = "wizard.create.check"
#    
#    def default_get(self, cr, uid, fields, context=None):
#        if context is None:
#            context = {}
#        res = super(wizard_create_check, self).default_get(cr, uid, fields, context=context)
#        record_ids = context and context.get('active_ids', False) or False
#        invoice_obj = self.pool.get('account.invoice')
#        
#        for inv in invoice_obj.browse(cr, uid, record_ids, context=context):
#
#            if 'invoice_state' in fields:
#                res['invoice_state'] = 'none'
#            
#        return res
#    
#    _columns = {
#        'name':fields.char('Memo', size=256),
#        'date':fields.date('Date'),
#        'journal_id':fields.many2one('account.journal', 'Journal'),
#        
#        'period_id': fields.many2one('account.period', 'Period', required=True),
#        'partner_id': fields.many2one('res.partner', 'Supplier', required=True),
#        'narration':fields.text('Notes'),
#        'bank_id': fields.many2one('res.partner.bank', 'Bank', required=True, domain="[('partner_id','=',partner_id)]"),
#
#        'company_id': fields.many2one('res.company', 'Company', required=True),
#         
#    }
#    
#    _defaults = {
#        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
#    }
#    
#    def action_check_create(self, cr, uid, ids, context=None):
#        
#        return {'type': 'ir.actions.act_window_close'}
#
#wizard_create_checK()