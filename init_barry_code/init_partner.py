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
import urllib
import csv
import openerp.addons.decimal_precision as dp


class res_partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
    'account_number': fields.char('Account Number', 64),
    }
    
    _sql_constraints = [
        ('account_number_uniq', 'unique (account_number)', 'The account number of partner must be unique!')
    ]
    
    def create(self, cr, uid, vals, context=None):
        if not 'account_number' in vals or not vals['account_number']:
            vals.update({'account_number': self.pool.get('ir.sequence').get(cr, uid, 'init.res.partner')})
        return super(res_partner, self).create(cr, uid, vals, context)
    
res_partner()

class init_config_import_payment(osv.osv):
    _name = "init.config.import.payment"
    _columns = {
    'name': fields.char('URL', size=128, required=True),
    'file_name': fields.char('Filename', size=128),
    'dynamic_name': fields.boolean('Dynamic Name'),
    'dynamic_file_name': fields.selection([('ymd','YYMMDD'), ('mdy','MMDDYY'), ('dmy','DDMMYY')], 'Date Type'),
    'journal_id': fields.many2one('account.journal', 'Journal', required=True),
    'company_id': fields.many2one('res.company', 'Company'),
    }    
    
    _defaults = {
                 'company_id' : lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
                 }
    
    def process_import(self, cr, uid, ids, context={}):
        voucher_obj = self.pool.get('account.voucher')
        partner_obj = self.pool.get('res.partner')
        journal_obj = self.pool.get('account.journal')
        date = False
        ids = self.search(cr, uid, [])
        for record in self.browse(cr, uid, ids):
            name = record.name
            if record.name[len(record.name)-1:] != '/':
                name += '/'
            if not record.dynamic_name:
                name += record.file_name
            else:
                if record.dynamic_file_name == 'ymd':
                    name += time.strftime('%Y%m%d') + '.txt'
                elif record.dynamic_file_name == 'mdy':
                    name += time.strftime('%m%d%Y') + '.txt'
                else:
                    name += time.strftime('%d%m%Y') + '.txt'
                    
            urllib.urlretrieve(name)
            res = {}
            with open(record.file_name, 'rb') as txtfile:
                spamreader = csv.reader(txtfile, delimiter=',', quotechar='|')
                for row in spamreader:
                    
                    partner_id = partner_obj.search(cr, uid, [('account_number', '=', row[1].replace('"',''))])
                    partner_id = partner_id and partner_id[0] or False                    
                    if not partner_id:
                        raise osv.except_osv('Error!',"Not find customer for account number: %s."%row[1])
                    amount = float(row[3].replace('"',''))                                   
                    date = row[2].replace('"','')
                    date = '%s-%s-%s'%(date[:4], date[4:6], date[6:])
                    name = row[4].replace('"','')
                    company_id = partner_obj.browse(cr, uid, partner_id).company_id.id
                    voucher_vals = {
                                    'partner_id': partner_id,
                                    'amount': amount,
                                    'date' : date,
                                    'name' : name,
                                    'company_id': company_id,
                                    'type': 'receipt',
                                    }
                    journal_ids = record.journal_id and [record.journal_id.id] or []
                    #journal_ids = journal_obj.search(cr, uid, [('company_id', '=', company_id),('type', '=', 'bank')])
                    if not journal_ids:
                        raise osv.except_osv('Error!',"Not find journal with type = 'bank' for company: %s."%partner_obj.browse(cr, uid, partner_id).company_id.name)
                    voucher_vals.update(self.pool.get('account.voucher').onchange_partner_id(cr, uid, [],
                                    partner_id=partner_id,
                                    journal_id=journal_ids[0],
                                    amount=amount,
                                    currency_id=partner_obj.browse(cr, uid, partner_id).company_id.currency_id.id,
                                    ttype='receipt',
                                    date=date,
                                    context=context
                                )['value'])
                    line_cr_ids = []
                    for line_dr in voucher_vals['line_cr_ids']:
                        line_cr_ids.append((0, 0, line_dr))
                    voucher_vals['line_cr_ids'] = line_cr_ids
                    voucher_vals['line_dr_ids'] = []
                    
                    voucher_obj.create(cr, uid, voucher_vals)

        return {}
init_config_import_payment()

class init_allocation_charge(osv.osv):
    _name = "init.allocation.charge"
    _columns = {
    'name': fields.char('Name', size=128, required=True, readonly=True, states={'draft':[('readonly',False)]}),
    'amount': fields.float('Amount', readonly=True, states={'draft':[('readonly',False)]}),
    'remain': fields.integer('Remaining Month'),
    'month': fields.integer('Months', readonly=True, states={'draft':[('readonly',False)]}),
    'period_id': fields.many2one('account.period', 'Allocation from Period', required=True, readonly=True, states={'draft':[('readonly',False)]}),
    'partner_id': fields.many2one('res.partner', 'Partner', required=True, readonly=True, states={'draft':[('readonly',False)]}),
    'state': fields.selection([('draft','Draft'), ('done','Validate')], 'Status', readonly=True),
    'company_id': fields.many2one('res.company', 'Company', readonly=True, states={'draft':[('readonly',False)]}),
    'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
    'account_credit_id': fields.many2one('account.account', 'Account Credit', required=True, ondelete="cascade", domain="[('type','<>','view'), ('type', '<>', 'closed'),('company_id','=', company_id)]", readonly=True, states={'draft':[('readonly',False)]}),    
    'account_debit_id': fields.many2one('account.account', 'Account Debit', required=True, ondelete="cascade",  domain="[('type','<>','view'), ('type', '<>', 'closed'),('company_id','=', company_id)]", readonly=True, states={'draft':[('readonly',False)]}),
    }    
    
    _defaults = {
                 'company_id' : lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
                 'state' : 'draft',
                 }
    
    def action_validate(self, cr, uid, ids, context={}):
        for obj in self.browse(cr, uid, ids):
            date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            period_id = self.pool.get('account.period').search(cr,uid,[('date_start','<=',date),('date_stop','>=',date)]) 
            if obj.period_id.id in period_id and obj.remain != obj.month:            
                self.allocation_charge(cr, uid, [obj.id], context)
            
        return self.write(cr, uid, ids, {'state': 'done'})
    
    def allocation_charge(self, cr, uid, ids, context={}):
        for obj in self.browse(cr, uid, ids):
            amount = round(obj.amount / obj.month)
            self.write(cr, uid, [obj.id],{'remain': obj.remain + 1})
            date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            period_id = self.pool.get('account.period').search(cr,uid,[('date_start','<=',date),('date_stop','>=',date)]) 
            data = self.create_move_line(cr, uid, obj.name, amount, obj.account_credit_id.id, obj.account_debit_id.id, obj.journal_id.id, \
                                         period_id[0], date, obj.partner_id.id, context)
            self.create_account_move(cr, uid, ids, obj.journal_id.id, obj.name, date, period_id[0], data, context)
        return {}
    
    def auto_allocation_charge(self, cr, uid, ids, context={}):
        #ids = self.search(cr, uid, [('month - remain', '>', 0)])
        sql = 'select id from init_allocation_charge where month - remain > 0'
        cr.execute(sql)
        dict = cr.dictfetchall()
        ids = [d['id'] for d in dict]
        self.allocation_charge(cr, uid, ids, context)
        return {}
    
    def create_move_line(self, cr, uid,\
                                   name, \
                                   amount,account_crebit, \
                                   account_debit,journal_id,\
                                   period_id, date, \
                                   partner_id, context):        
                    
        result = []
        if account_crebit and account_debit: # and amount_cost_price > 0:
           
            move_line1 = {
                'name'                  : name ,
                'debit'                 : 0,
                'credit'                : amount,
                'account_id'            : account_crebit,
                'journal_id'            : journal_id,
                'period_id'             : period_id,
                'quantity'              : 1,
                'date'                  : date,
                'partner_id'            : partner_id,
            }
            result.append((0, 0, move_line1))
            move_line2 = {
                'name'                  : name,
                'debit'                 : amount,
                'credit'                : 0,
                'account_id'            : account_debit,
                'journal_id'            : journal_id,
                'period_id'             : period_id,
                'quantity'              : 1,
                'date'                  : date,
                'partner_id'            : partner_id,
            }
            result.append((0, 0, move_line2))
            
        return result
    
    def create_account_move(self, cr, uid, ids, \
                                   journal_id, \
                                   name, \
                                   date, period_id, data, context):
       
        move_pool = self.pool.get('account.move')
        move = {
                'ref': name,
                'name': name,
                'journal_id': journal_id,
                'date': date,
                'date_document': date,
                'period_id':period_id,
                'line_id' : data,
            }
        move_id = move_pool.create(cr, uid, move, context=context)
        return move_id
init_allocation_charge()


