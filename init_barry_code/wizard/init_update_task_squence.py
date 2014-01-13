# -*- coding: utf-8 -*-
##############################################################################
#
#    Thesis bike shop
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime
import urllib
import csv
import time

class init_update_task_squence(osv.osv_memory):
    _name = "init.update.task.squence"
    
    _columns = {
        'amount': fields.float('Amount Compensation'),
        'task_value': fields.float('Task Value'),
        'tasks_ahead': fields.float('Tasks Ahead'),
    }
    
    def onchange_amount(self, cr, uid, ids, amount, context):
        result = 0
        customer_id = False
        task_id = context.get('active_id', False)
        
        task_obj = self.pool.get('project.task')
        inoive_obj = self.pool.get('account.invoice')
        company_obj = self.pool.get('res.company')
        company_ids = company_obj.search(cr, uid, [('parent_id','=', False)])
        if company_ids and len(company_ids) == 1:
            customer_id = company_obj.browse(cr, uid, company_ids)[0].partner_id.id
        ids = self.search(cr, uid, []) 
        if task_id:
            obj = task_obj.browse(cr, uid, task_id)
            
            invoice_ids = inoive_obj.search(cr, uid, [('company_id','=', obj.company_id.id), ('partner_id', '=', customer_id)], limit=1)
            mana_fee = 0
            if invoice_ids:
                mana_fee = inoive_obj.browse(cr, uid, invoice_ids)[0].amount_total
            
            task_ids = task_obj.search(cr, uid, [('company_id','=', obj.company_id.id),('state', 'not in', ('done', 'cancel'))])
            number_task = len(task_ids)
            if number_task == 0:
                result = 0
                return  {'value': {'tasks_ahead': 0}}
            
            now = datetime.now()  
            duration = now - datetime.strptime(obj.create_date, '%Y-%m-%d %H:%M:%S')
            days, seconds = duration.days, duration.seconds
            hours = days * 24 + seconds // 3600
            result = (mana_fee + amount) / number_task * int(hours)
            sql = ''' select id from project_task where state not in ('done', 'cancel') and sort_task_value > %s ''' %result
            cr.execute(sql)
            task_ids = cr.fetchall()       
            return  {'value': {'tasks_ahead': len(task_ids), 'task_value': result}} 
        return  {'value': {'tasks_ahead': 0}}
    
    def action_validate(self, cr, uid, ids, context={}):
        
        task_obj = self.pool.get('project.task')
        task_id = context.get('active_id', False)
        if not task_id:
            return {}
        for obj in self.browse(cr, uid, ids):
            task_obj.write(cr, uid, [task_id], {'amount' : obj.amount + task_obj.browse(cr, uid, task_id).amount,
                                                'task_value' : obj.task_value,
                                                'tasks_ahead': obj.tasks_ahead})

        return {'type': 'ir.actions.act_window_close'}
    

