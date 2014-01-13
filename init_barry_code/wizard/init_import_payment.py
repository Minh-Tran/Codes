# -*- coding: utf-8 -*-
##############################################################################
#
#    Thesis bike shop
#
##############################################################################

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT,\
                               DEFAULT_SERVER_DATETIME_FORMAT
import datetime
import urllib
import csv
import time

class init_import_payment(osv.osv_memory):
    _name = "init.import.payment"
    
    _columns = {
        'name': fields.char('URL', size=128, required=True),
        'file_name': fields.char('Filename', size=128),
    }
    
    def process_import(self, cr, uid, ids, context={}):
        voucher_obj = self.pool.get('account.voucher')
        partner_obj = self.pool.get('res.partner')
        journal_obj = self.pool.get('account.journal')
        date = False
        for record in self.browse(cr, uid, ids):
            name = record.name
            if record.name[len(record.name)-1:] != '/' and record.file_name:
                name += '/'
            name += record.file_name and record.file_name or ''
            urllib.urlretrieve(name)
            
            res = {}
            if 'file:///' == name[:8]:
                name = name[8:]
            with open(name, 'rb') as txtfile:
                spamreader = csv.reader(txtfile, delimiter=',', quotechar='|')
                for row in spamreader:
                    if len(row) == 2:
                        continue
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
                    journal_ids = journal_obj.search(cr, uid, [('company_id', '=', company_id),('type', '=', 'bank')])
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
                    print voucher_vals
                    voucher_obj.create(cr, uid, voucher_vals)

        return {'type': 'ir.actions.act_window_close'}
    

