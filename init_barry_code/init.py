# -*- encoding: utf-8 -*-
##############################################################################
#
#    INIT TECH, Open Source Management Solution
#    Copyright (C) 2012 General Solutions (<http://init.vn>). All Rights Reserved
#
##############################################################################

from datetime import datetime
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp

_intervalTypes = {
    'work_days': lambda interval: relativedelta(days=interval),
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'property_account_income_partner': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Income Account",
            view_load=True,
            domain="[('company_id','=', id)]",
            help="This account will be used for invoices to value charges."),
        'property_account_expense_partner': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Income Account",
            view_load=True,
            domain="[('company_id','=', id)]",
            help="This account will be used for invoices to value charges."),
    }
    
res_company()

class res_partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
    'board_member': fields.boolean('Board Member'),
	'owner_occupied': fields.boolean('Owner Occupied'),                   
    'property_account_payable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Payable",
            view_load=True,
            domain="[('type', '=', 'payable'),('company_id','=', company_id)]",
            help="This account will be used instead of the default one as the payable account for the current partner",
            required=True),
    'property_account_receivable': fields.property(
        'account.account',
        type='many2one',
        relation='account.account',
        string="Account Receivable",
        view_load=True,
        domain="[('type', '=', 'receivable'),('company_id','=', company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner"),
    }
    
res_partner()

class init_common_interest(osv.osv):
    _name = "init.common.interest"
    _columns = {
    'company_id': fields.many2one('res.company','Company', domain="[('parent_id','!=',False)]"),
    'user_id': fields.many2one('res.users','User Create'),
    'name': fields.char('Description', required=True),    
    'line_ids': fields.one2many('init.common.interest.line', 'order_id', '% Common Interest'),
    'shares_line_ids': fields.one2many('init.common.interest.line', 'order_id', '% Common Interest'),
    'type': fields.selection([('percent','Percent(%)'),('shares','Shares')],'Type'),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'type': lambda *a: 'percent',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    
    def _check_percent(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            total = 0
            for line in order.line_ids:
                total += line.percent
            if (total > 100 or total > 100.00) and order.type == 'percent':
                return False
        return True

    _constraints = [
        (_check_percent, 'Error! Total percent <= 100.', ['line_ids'])
    ]
    
init_common_interest()

class init_common_interest_line(osv.osv):
    _name = "init.common.interest.line"
    _columns = {
    'partner_id': fields.many2one('res.partner','Partner', domain="[('customer','=',True)]", required=True),
    'order_id': fields.many2one('init.common.interest','Parent'),
    'company_id': fields.related('order_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
    'percent': fields.float('Percent', digits_compute=dp.get_precision('Percent')),   
    }
    
init_common_interest_line()


class init_probility_charge(osv.osv):
    _name = "init.probility.charge"
    _columns = {
    'interest_id': fields.many2one('init.common.interest','Common Interest', domain="[('company_id','=',company_id)]", required=True, readonly=True, states={'draft': [('readonly', False)]}),
    'company_id': fields.many2one('res.company','Company', domain="[('parent_id','!=',False)]"),
    'currency_id': fields.many2one('res.currency','Currency', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    'user_id': fields.many2one('res.users','User Create'),
    'type': fields.related('interest_id', 'type', type='selection', selection= [('percent','Percent(%)'),('shares','Shares')], 
                                                                                                   string='Type', readonly=True),
    'date_invoice': fields.date('Invoice Date', readonly=True, states={'draft': [('readonly', False)]}),
    'property_account_receivable': fields.property(
        'account.account',
        type='many2one',
        relation='account.account',
        string="Account Receivable",
        view_load=True,
        domain="[('type', '=', 'receivable'),('company_id','=', company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner"),
    'property_account_income_partner': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Income Account",
            view_load=True,
            domain="[('company_id','=', company_id)]", required=True, readonly=True, states={'draft': [('readonly', False)]},
            help="This account will be used for invoices to value charges."),
    'value_charge': fields.float('Charge', readonly=True, states={'draft': [('readonly', False)]}),
    'name': fields.char('Description', required=True, readonly=True, states={'draft': [('readonly', False)]}),    
    'line_ids': fields.one2many('init.probility.charge.line', 'order_id', 'Probility Charge', readonly=True, states={'draft': [('readonly', False)]}),
    'state': fields.selection([('draft','Draft'), ('confirm','Approve'), ('invoiced','Invoiced'), ('cancel','Closed')], 'Status', readonly=True),
    'auto_month': fields.boolean('Is Auto Month',),
    'interval_number': fields.integer('Interval Number',help="Repeat every x."),
    'interval_type': fields.selection( [('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Interval Unit'),
    'numbercall': fields.integer('Number of Calls', help='How many times the method is called,\na negative number indicates no limit.'),
    'nextcall' : fields.date('Next Execution Date', required=True, help="Next planned execution date for this job."),
    'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': lambda self, cr, uid, context: True,
        'user_id': lambda self, cr, uid, context: uid,
        'state': 'draft',
        'nextcall' : lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        'interval_number' : 1,
        'interval_type' : 'months',
        'numbercall' : 1,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.currency_id.id,
    }
    
    def onchange_company_id(self, cr, uid, ids, company_id):
        if not company_id:
            return {'value': {}}
        
        account_ids = self.pool.get('account.account').search(cr, uid,
                                        [('type', '=', 'receivable'), ('company_id', '=', company_id)])
        if not account_ids:
            raise osv.except_osv(_('Error!'),
            _('Please define receivable account for this company: "%s" (id:%d).') % (company_id, company_id))
        return {'value': {'property_account_receivable': account_ids and account_ids[0] or False}}
    
    def action_compute(self, cr, uid, ids, context):
        obj_line = self.pool.get('init.probility.charge.line')
        for obj in self.browse(cr, uid, ids):
#            total = 0
            cr.execute('delete from init_probility_charge_line where order_id=%s ', (obj.id,))
            for line in obj.interest_id.line_ids:
                amount = 0
                if obj.interest_id and obj.interest_id.type == 'percent':
                    amount = round(obj.value_charge * line.percent /100,2)
#                    if line != obj.interest_id.line_ids[len(obj.interest_id.line_ids)-1]:
#                        total += amount
#                    else:
#                        amount = obj.value_charge - total
                else:
                    amount = obj.value_charge * line.percent
                obj_line.create(cr, uid, {
                                          'partner_id' : line.partner_id.id,
                                          'percent' : line.percent,
                                          'order_id' : obj.id,
                                          'amount' : amount,
                                          })
        return True
    
    def action_confirm(self, cr, uid, ids, context):
        self.action_compute(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'confirm'})
        return True
    
    def action_run_scheduler_invoice(self, cr, uid, ids, context):
        ids = self.search(cr, uid, [('state','in',('confirm','invoiced')), ('auto_month','=',True)])
        for job in self.browse(cr, uid, ids):        
            self._process_job(cr,uid, job, {})
            date_invoice = datetime.strptime(job.date_invoice, DEFAULT_SERVER_DATE_FORMAT)
            self.write(cr, uid, [job.id], {'date_invoice':(date_invoice + relativedelta(months=1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                                           'state': 'confirm'})
        return True
    
    def _process_job(self, cr, uid, job, context):
        now = datetime.now() 
        nextcall = datetime.strptime(job.nextcall, DEFAULT_SERVER_DATE_FORMAT)
        numbercall = job.numbercall

        ok = False
        while nextcall <= now and numbercall:
            if numbercall > 0:
                numbercall -= 1
            self.action_invoice_create(cr, uid, [job.id], context)
            if numbercall:
                nextcall += _intervalTypes[job.interval_type](job.interval_number)
            ok = True
        addsql = ''
        if not numbercall:
            addsql = ', active=False'
        cr.execute("UPDATE init_probility_charge SET nextcall=%s, numbercall=%s"+addsql+" WHERE id=%s",
                   (nextcall.strftime(DEFAULT_SERVER_DATE_FORMAT), numbercall, job['id']))

    
    def _prepare_invoice(self, cr, uid, order, line, lines, context=None):

        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        
        property_account_receivable = False
        if line.partner_id.property_account_receivable:
            property_account_receivable = line.partner_id.property_account_receivable.id
        if not property_account_receivable:
            property_account_receivable = context.get('property_account_receivable', False)
        if not property_account_receivable and order.property_account_receivable:
            property_account_receivable = order.property_account_receivable.id
        
        invoice_vals = {
            'name': order.name or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.name,
            'date_invoice': order.date_invoice or False,
            'account_id': property_account_receivable,
            'partner_id': line.partner_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.currency_id.id,
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False
        }

        return invoice_vals
    
    def action_invoice_create(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        
        obj_line = self.pool.get('init.probility.charge.line')
        invoice_ids = []
        for obj in self.browse(cr, uid, ids):
            property_account_receivable = obj.property_account_receivable and obj.property_account_receivable.id or False
            if not property_account_receivable:
                for line in obj.line_ids:
                    if not line.partner_id.property_account_receivable:
                        account_ids = self.pool.get('account.account').search(cr, uid,
                                            [('type', '=', 'receivable'), ('company_id', '=', obj.company_id.id)])
                        if not account_ids:
                            raise osv.except_osv(_('Error!'),
                            _('Please define receivable account for this company: "%s" (id:%d).') % (obj.company_id.name, obj.company_id.id))
                        elif len(account_ids) == 1:
                            property_account_receivable = account_ids[0]
                            break
                        else:
                            ir_model_data = self.pool.get('ir.model.data')
                            form_res = ir_model_data.get_object_reference(cr, uid, 'init_barry_code', 'view_init_bulk_charge_make_invoice')
                            form_id = form_res and form_res[1] or False
                            return {
                                'name': _('Make Invoice'),
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'init.bulk.charge.make.invoice',
#                                'view_id': False,
#                                'views': [(form_id, 'form')],
                                'context': {'company_id': obj.company_id.id, 'bulk_ids': ids},
                                'target' : 'new',
                                'type': 'ir.actions.act_window',
                            }
            for line in obj.line_ids:                
                lines = obj_line. invoice_line_create(cr, uid, [line.id], context)
                vals = self._prepare_invoice(cr, uid, obj, line, lines, dict(context, property_account_receivable = property_account_receivable))                
                invoice_id = self.pool.get('account.invoice').create(cr, uid, vals)
                invoice_ids += [int(invoice_id)]
        if context.get('open_invoice', False):
            self.write(cr, uid, ids, {'state': 'invoiced'})
            return self.open_invoices(cr, uid, ids, invoice_ids, context)
        return True
        
    def open_invoices(self, cr, uid, ids, invoice_ids, context=None):
        """ open a view on one of the given invoice_ids """
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'domain': ''' [('id','in', %s)] '''%invoice_ids,
            'view_id': False,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'context': {'type': 'out_invoice'},
            'type': 'ir.actions.act_window',
        }
    
    def action_cancel(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True
    
init_probility_charge()

class init_probility_charge_line(osv.osv):
    _name = "init.probility.charge.line"
    _columns = {
    'partner_id': fields.many2one('res.partner','Partner', domain="[('customer','=',True),('property_account_income_partner','!=',False)]"),
    'order_id': fields.many2one('init.probility.charge','Parent'),
    'company_id': fields.related('order_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
    'percent': fields.float('Percent', digits_compute=dp.get_precision('Percent')),   
    'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),   
    }
    
    def _prepare_order_line_invoice_line(self, cr, uid, order, line, account_id=False, context=None):
        
        res = {}
        if not account_id:
            if order.property_account_income_partner:
                account_id = order.property_account_income_partner.id
                if not account_id:
                    account_id = order.company_id.property_account_income_partner.id
                if not account_id:
                    raise osv.except_osv(_('Error!'),
                            _('Please define income account for this partner: "%s" (id:%d).') % \
                                (line.partner_id.name, line.partner_id.id,))
           
            res = {
                'name': order.company_id.name,
                'account_id': account_id,
                'price_unit': line.amount,
                'quantity': 1,
            }

        return res
    
    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_invoice_line(cr, uid, line.order_id, line, False, context)
            if vals:
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)                
                create_ids.append(inv_id)

        return create_ids
    
init_probility_charge_line()


