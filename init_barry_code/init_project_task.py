# -*- encoding: utf-8 -*-
##############################################################################
#
#    INIT TECH, Open Source Management Solution
#    Copyright (C) 2012 INIT TECH (<http://init.vn>). All Rights Reserved
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import tools
from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class project_task(osv.osv):
    _name = "project.task"
    _inherit = "project.task"
    
    def __compute_task_value(self, cr, uid, ids, field_name, arg=None, context=None):
        result = {}
        company_id = False
        inoive_obj = self.pool.get('account.invoice')
        sql = ''' select id from res_company where parent_id is null '''
        cr.execute(sql)
        company_ids  = cr.fetchall()            
        if company_ids and len(company_ids) == 1:
            company_id = company_ids[0]
            
        for obj in self.browse(cr, uid, ids):
            if obj.state in ('done', 'cancel'):
                result[obj.id] = 0
                continue
            
            result[obj.id] = 0.0
            invoice_ids = inoive_obj.search(cr, uid, [('company_id','=', company_id), ('partner_id', '=', obj.company_id.partner_id.id)], limit=1)
            mana_fee = 0
            if invoice_ids:
                mana_fee = inoive_obj.browse(cr, uid, invoice_ids)[0].amount_total
            
            task_ids = self.search(cr, uid, [('company_id','=', obj.company_id.id),('state', 'not in', ('done', 'cancel'))])
            number_task = len(task_ids)
            if number_task == 0:
                result[obj.id] = 0
                continue
            
            now = datetime.now()  
            duration = now - datetime.strptime(obj.create_date, '%Y-%m-%d %H:%M:%S')
            days, seconds = duration.days, duration.seconds
            hours = days * 24 + seconds // 3600
            result[obj.id] = (mana_fee + obj.amount) / number_task * int(hours)
        return result
    
    def __compute_tasks_head_value(self, cr, uid, ids, field_name, arg=None, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids):
            
            sql = ''' select id from project_task where state not in ('done', 'cancel') and sequence > %s ''' %obj.sequence
            cr.execute(sql)
            task_ids = cr.fetchall()            
            result[obj.id] = len(task_ids)
        return result
    
    _columns = {
        'task_value': fields.function(__compute_task_value, digits_compute=dp.get_precision('Account'), string='Task Value (Immediately)'),
        'tasks_ahead': fields.function(__compute_tasks_head_value, type='integer', string='Tasks Ahead'),
        'amount': fields.float('Amount Compensation (Schedule)'),
        'sort_task_value': fields.float('Task Value'),
    }
    
    _order = "sequence desc"
    
    def _update_compute_seq_value(self, cr, uid, ids, context=None):
        result = {}
        company_id = False
        inoive_obj = self.pool.get('account.invoice')
        company_obj = self.pool.get('res.company')
        company_ids = company_obj.search(cr, uid, [('parent_id','=', False)])
        if company_ids and len(company_ids) == 1:
            company_id = company_ids[0]
        
        ids = self.search(cr, uid, [('state','not in', ('done', 'cancel'))]) 
        for obj in self.browse(cr, uid, ids):
                        
            result[obj.id] = 0.0
            if not obj.company_id.partner_id:
                continue
            
            invoice_ids = inoive_obj.search(cr, uid, [('company_id','=', company_id), ('partner_id', '=', obj.company_id.partner_id.id)], limit=1)
            mana_fee = 0
            if invoice_ids:
                mana_fee = inoive_obj.browse(cr, uid, invoice_ids)[0].amount_total
            
            task_ids = self.search(cr, uid, [('company_id','=', obj.company_id.id),('state', 'not in', ('done', 'cancel'))])
            number_task = len(task_ids)
            if number_task == 0:
                result[obj.id] = 0
                continue
            
            now = datetime.now()  
            duration = now - datetime.strptime(obj.create_date, '%Y-%m-%d %H:%M:%S')
            days, seconds = duration.days, duration.seconds
            hours = days * 24 + seconds // 3600
            result[obj.id] = (mana_fee + obj.amount) / number_task * int(hours)
        import operator
        sorted_result = sorted(result.iteritems(), key=operator.itemgetter(1))
        seq = 1
        ids = []
        for temp in sorted_result:
            if temp[1] == 0:
                ids.append(temp[0])
                continue
            
            self.write(cr, uid, [temp[0]], {'sequence': seq, 'sort_task_value': temp[1]})
            seq += 1
        ids += self.search(cr, uid, [('state','in', ('done', 'cancel')), ('sequence', '>', 0)]) 
        self.write(cr, uid, ids, {'sequence': 0})
        return True    
            
project_task()


