##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from openerp.report import report_sxw
from openerp.addons.account.report.common_report_header import common_report_header
from openerp.tools.translate import _
from openerp.addons.account.report import account_financial_report

class report_account_common_inherit(report_sxw.rml_parse, common_report_header):

    def __init__(self, cr, uid, name, context=None):
        super(report_account_common_inherit, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'get_lines': self.get_lines,
            'get_lines_income': self.get_lines_income,
            'get_management_company': self.get_management_company,
            'time': time,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_filter': self._get_filter,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_period': self.get_period,
            'name_period': self.name_period,
            'name_fy': self.name_fy,
            'name_company': self.name_company,
        })
        self.context = context
        
    def name_company(self, fy_id):
        cr = self.cr
        uid = self.uid
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fy = fiscalyear_obj.browse(cr, uid, fy_id)
        return fy.company_id.name
    
    def name_fy(self, fy_id):
        cr = self.cr
        uid = self.uid
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fy = fiscalyear_obj.browse(cr, uid, fy_id)
        ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
        return ds.strftime('%Y')
        
    def name_period(self, fy_id, month):
        cr = self.cr
        uid = self.uid
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        return fiscalyear_obj.browse(cr, uid, fy_id[0]).period_ids[month].name

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(report_account_common_inherit, self).set_context(objects, data, new_ids, report_type=report_type)
    
    def _get_children_by_order(self, cr, uid, ids, context=None):
        '''returns a dictionary with the key= the ID of a record and value = all its children,
           computed recursively, and sorted by sequence. Ready for the printing'''
        res = []
        for id in ids:
            res.append(id)
            ids2 = self.pool.get('account.financial.report').search(cr, uid, [('parent_id', '=', id)], order='sequence,id ASC', context=context)
            res += self._get_children_by_order(cr, uid, ids2, context=context)
        return res
    
    def get_management_company(self):
        company_obj = self.pool.get('res.company')
        comp_ids = company_obj.search(self.cr, 1, [('parent_id','=', False)])
        if comp_ids:
            return company_obj.browse(self.cr, self.uid, comp_ids)[0]
        return False

    def get_lines(self, data):
        lines = []
        lines2 = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        ids2 = self._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=data['form']['used_context'])
        if data['form']['report_method'] == 'accrual': 
            for report in self.pool.get('account.financial.report').browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
                vals = {
                    'name': report.name,
                    'balance': report.balance * report.sign or 0.0,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                lines.append(vals)
                account_ids = []
                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    lines2.append({
                                'name': 'Total %s'%report.name,
                                'balance': report.balance * report.sign or 0.0,
                                'type': 'report',
                                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                                'account_type': True, #used to underline the financial report balances
                            })
                    continue
                if report.type == 'accounts' and report.account_ids:
                    account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
                elif report.type == 'account_type' and report.account_type_ids:
                    account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
                if account_ids:
                    
                    child_lines = []
                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance != 0 and account.balance * report.sign or account.balance,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                        }
    
                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            child_lines.append(vals)
                    #insert line total into file report
                    total_line = {}
                    new_child_lines = []
                    for line in child_lines:
                        new_line =  dict(line)
                        new_child_lines.append(new_line)
                        if line.get('account_type', False) == 'view':
                            if line != child_lines[0]:
                                new_child_lines.append(total_line)
                            total_line = line
                            total_line['name'] = 'Total %s'%total_line['name']
                            total_line['account_type'] = True
                    new_child_lines.append(total_line)
                    lines += new_child_lines   
                    #------------------------------------------------------
                lines.append({
                    'name': 'Total %s'%report.name,
                    'balance': report.balance * report.sign or 0.0,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': True, #used to underline the financial report balances
                })
            from operator import itemgetter
            lines2 =  sorted(lines2, key=itemgetter('level'), reverse=True)
            lines += lines2
    #        print lines
        elif data['form']['report_method'] == 'cash':
            for report in self.pool.get('account.financial.report').browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
                vals = {
                    'name': report.name,
                    'balance': report.balance_cash * report.sign or 0.0,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance_cash * report.sign or 0.0
                lines.append(vals)
                account_ids = []
                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    lines2.append({
                                'name': 'Total %s'%report.name,
                                'balance': report.balance_cash * report.sign or 0.0,
                                'type': 'report',
                                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                                'account_type': True, #used to underline the financial report balances
                            })
                    continue
                if report.type == 'accounts' and report.account_ids:
                    account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
                elif report.type == 'account_type' and report.account_type_ids:
                    account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
                if account_ids:
                    
                    child_lines = []
                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance_cash != 0 and account.balance_cash * report.sign or account.balance_cash,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                        }
    
                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance_cash * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            child_lines.append(vals)
                    #insert line total into file report
                    total_line = {}
                    new_child_lines = []
                    for line in child_lines:
                        new_line =  dict(line)
                        new_child_lines.append(new_line)
                        if line.get('account_type', False) == 'view':
                            if line != child_lines[0]:
                                new_child_lines.append(total_line)
                            total_line = line
                            total_line['name'] = 'Total %s'%total_line['name']
                            total_line['account_type'] = True
                    new_child_lines.append(total_line)
                    lines += new_child_lines   
                    #------------------------------------------------------
                lines.append({
                    'name': 'Total %s'%report.name,
                    'balance': report.balance_cash * report.sign or 0.0,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': True, #used to underline the financial report balances
                })
            from operator import itemgetter
            lines2 =  sorted(lines2, key=itemgetter('level'), reverse=True)
            lines += lines2
        return lines
    
    def get_period(self, ids, context=None, interval=1):
        cr = self.cr
        uid = self.uid
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        periods = []
        for fy in fiscalyear_obj.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                periods.append({
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                })
                ds = ds + relativedelta(months=interval)
        return periods
    
    def get_lines_income(self, data):
        lines = []
        lines2 = []
        income_lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        ids2 = self._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=data['form']['used_context'])
        
        fiscalyear_id = data['form']['fiscalyear_id']
        
        periods = self.get_period([fiscalyear_id], {}, 3)
        
        
        dict_1 = dict(data['form']['used_context'])
        dict_1['date_from'] = periods[0]['date_from']
        dict_1['date_to'] = periods[0]['date_to']
        
        dict1 = dict(data['form']['used_context'])
        dict1['date_from'] = periods[1]['date_from']
        dict1['date_to'] = periods[1]['date_to']
        
        dict2 = dict(data['form']['used_context'])
        dict2['date_from'] = periods[2]['date_from']
        dict2['date_to'] = periods[2]['date_to']
        
        dict3 = dict(data['form']['used_context'])
        dict3['date_from'] = periods[3]['date_from']
        dict3['date_to'] = periods[3]['date_to']
        
        if not data['form']['used_context'].get('date_from'):        
            data['form']['used_context']['date_from'] = periods[0]['date_from']
        if not data['form']['used_context'].get('date_to'):
            data['form']['used_context']['date_to'] = periods[3]['date_to']
        
        if data['form']['interval'] == 'month':
            return self.get_lines_income_month(data)
        elif data['form']['interval'] == 'year':
            return self.get_lines(data)
        
        financial_report_obj = self.pool.get('account.financial.report')
        if data['form']['report_method'] == 'accrual':
            for report in financial_report_obj.browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
                re_balance1 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict_1)
                re_balance2 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict1)
                re_balance3 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict2)
                re_balance4 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict3)
                vals = {
                    'name': report.name,
                    'balance': report.balance * report.sign or 0.0,
                    'balance1': re_balance1.balance != 0 and re_balance1.balance * report.sign or re_balance1.balance,
                    'balance2': re_balance2.balance != 0 and re_balance2.balance * report.sign or re_balance2.balance,
                    'balance3': re_balance3.balance != 0 and re_balance3.balance * report.sign or re_balance3.balance,
                    'balance4': re_balance4.balance != 0 and re_balance4.balance * report.sign or re_balance4.balance,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                
                account_ids = []
                if report.display_detail == 'no_detail':                
                    lines2.append({
                                'name': 'Total %s'%report.name,
                                'balance': report.balance * report.sign or 0.0,
                                'type': 'report',
                                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                                'account_type': True, #used to underline the financial report balances
                            })
                    continue
                else:
                    lines.append(vals)
                if report.type == 'accounts' and report.account_ids:
                    account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
                elif report.type == 'account_type' and report.account_type_ids:
                    account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
                if not account_ids:
                    lines.remove(vals)
                else:
                    
                    child_lines = []
                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        
                        balance1 = account_obj.browse(self.cr, self.uid, account.id, context=dict_1)
                        balance2 = account_obj.browse(self.cr, self.uid, account.id, context=dict1)
                        balance3 = account_obj.browse(self.cr, self.uid, account.id, context=dict2)
                        balance4 = account_obj.browse(self.cr, self.uid, account.id, context=dict3)
                        
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance != 0 and account.balance * report.sign or account.balance,
                            'balance1': balance1.balance != 0 and balance1.balance * report.sign or balance1.balance,
                            'balance2': balance2.balance != 0 and balance2.balance * report.sign or balance2.balance,
                            'balance3': balance3.balance != 0 and balance3.balance * report.sign or balance3.balance,
                            'balance4': balance4.balance != 0 and balance4.balance * report.sign or balance4.balance,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                        }
    
                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            child_lines.append(vals)
                    #insert line total into file report
                    total_line = {}
                    new_child_lines = []
                    for line in child_lines:
                        new_line =  dict(line)
                        new_child_lines.append(new_line)
                        if line.get('account_type', False) == 'view':
                            if line != child_lines[0]:
                                new_child_lines.append(total_line)
                            total_line = line
                            total_line['name'] = 'Total %s'%total_line['name']
                            total_line['account_type'] = True
                    new_child_lines.append(total_line)
                    lines += new_child_lines   
                    #------------------------------------------------------
                if lines:
                    lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance * report.sign or 0.0,
                        'balance1': re_balance1.balance != 0 and re_balance1.balance * report.sign or re_balance1.balance,
                        'balance2': re_balance2.balance != 0 and re_balance2.balance * report.sign or re_balance2.balance,
                        'balance3': re_balance3.balance != 0 and re_balance3.balance * report.sign or re_balance3.balance,
                        'balance4': re_balance4.balance != 0 and re_balance4.balance * report.sign or re_balance4.balance,
                        'type': 'report',
                        'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                        'account_type': True, #used to underline the financial report balances
                    })
                else:
                    income_lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance * report.sign or 0.0,
                        'balance1': re_balance1.balance != 0 and re_balance1.balance * report.sign or re_balance1.balance,
                        'balance2': re_balance2.balance != 0 and re_balance2.balance * report.sign or re_balance2.balance,
                        'balance3': re_balance3.balance != 0 and re_balance3.balance * report.sign or re_balance3.balance,
                        'balance4': re_balance4.balance != 0 and re_balance4.balance * report.sign or re_balance4.balance,
                        'type': 'report',
                        'level': 1,
                        'account_type': True, #used to underline the financial report balances
                    })
            from operator import itemgetter
            lines2 =  sorted(lines2, key=itemgetter('level'), reverse=True)
            lines += lines2
            lines += income_lines
        elif data['form']['report_method'] == 'cash':
            for report in financial_report_obj.browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
                re_balance1 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict_1)
                re_balance2 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict1)
                re_balance3 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict2)
                re_balance4 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict3)
                vals = {
                    'name': report.name,
                    'balance': report.balance_cash * report.sign or 0.0,
                    'balance1': re_balance1.balance_cash != 0 and re_balance1.balance_cash * report.sign or re_balance1.balance_cash,
                    'balance2': re_balance2.balance_cash != 0 and re_balance2.balance_cash * report.sign or re_balance2.balance_cash,
                    'balance3': re_balance3.balance_cash != 0 and re_balance3.balance_cash * report.sign or re_balance3.balance_cash,
                    'balance4': re_balance4.balance_cash != 0 and re_balance4.balance_cash * report.sign or re_balance4.balance_cash,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance_cash * report.sign or 0.0
                
                account_ids = []
                if report.display_detail == 'no_detail':                
                    lines2.append({
                                'name': 'Total %s'%report.name,
                                'balance': report.balance_cash * report.sign or 0.0,
                                'type': 'report',
                                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                                'account_type': True, #used to underline the financial report balances
                            })
                    continue
                else:
                    lines.append(vals)
                if report.type == 'accounts' and report.account_ids:
                    account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
                elif report.type == 'account_type' and report.account_type_ids:
                    account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
                if not account_ids:
                    lines.remove(vals)
                else:
                    
                    child_lines = []
                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        
                        balance1 = account_obj.browse(self.cr, self.uid, account.id, context=dict_1)
                        balance2 = account_obj.browse(self.cr, self.uid, account.id, context=dict1)
                        balance3 = account_obj.browse(self.cr, self.uid, account.id, context=dict2)
                        balance4 = account_obj.browse(self.cr, self.uid, account.id, context=dict3)
                        
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance_cash != 0 and account.balance_cash * report.sign or account.balance_cash,
                            'balance1': balance1.balance_cash != 0 and balance1.balance_cash * report.sign or balance1.balance_cash,
                            'balance2': balance2.balance_cash != 0 and balance2.balance_cash * report.sign or balance2.balance_cash,
                            'balance3': balance3.balance_cash != 0 and balance3.balance_cash * report.sign or balance3.balance_cash,
                            'balance4': balance4.balance_cash != 0 and balance4.balance_cash * report.sign or balance4.balance_cash,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                        }
    
                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance_cash * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            child_lines.append(vals)
                    #insert line total into file report
                    total_line = {}
                    new_child_lines = []
                    for line in child_lines:
                        new_line =  dict(line)
                        new_child_lines.append(new_line)
                        if line.get('account_type', False) == 'view':
                            if line != child_lines[0]:
                                new_child_lines.append(total_line)
                            total_line = line
                            total_line['name'] = 'Total %s'%total_line['name']
                            total_line['account_type'] = True
                    new_child_lines.append(total_line)
                    lines += new_child_lines   
                    #------------------------------------------------------
                if lines:
                    lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance_cash * report.sign or 0.0,
                        'balance1': re_balance1.balance_cash != 0 and re_balance1.balance_cash * report.sign or re_balance1.balance_cash,
                        'balance2': re_balance2.balance_cash != 0 and re_balance2.balance_cash * report.sign or re_balance2.balance_cash,
                        'balance3': re_balance3.balance_cash != 0 and re_balance3.balance_cash * report.sign or re_balance3.balance_cash,
                        'balance4': re_balance4.balance_cash != 0 and re_balance4.balance_cash * report.sign or re_balance4.balance_cash,
                        'type': 'report',
                        'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                        'account_type': True, #used to underline the financial report balances
                    })
                else:
                    income_lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance_cash * report.sign or 0.0,
                        'balance1': re_balance1.balance_cash != 0 and re_balance1.balance_cash * report.sign or re_balance1.balance_cash,
                        'balance2': re_balance2.balance_cash != 0 and re_balance2.balance_cash * report.sign or re_balance2.balance_cash,
                        'balance3': re_balance3.balance_cash != 0 and re_balance3.balance_cash * report.sign or re_balance3.balance_cash,
                        'balance4': re_balance4.balance_cash != 0 and re_balance4.balance_cash * report.sign or re_balance4.balance_cash,
                        'type': 'report',
                        'level': 1,
                        'account_type': True, #used to underline the financial report balances
                    })
            from operator import itemgetter
            lines2 =  sorted(lines2, key=itemgetter('level'), reverse=True)
            lines += lines2
            lines += income_lines
        data = lines
        if {} in lines:
            data = []
            for l in lines:
                if l: data.append(l)
        
        return data
    
    def get_lines_income_month(self, data):
        lines = []
        lines2 = []
        income_lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        ids2 = self._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=data['form']['used_context'])
        
        fiscalyear_id = data['form']['fiscalyear_id']
        
        periods = self.get_period( [fiscalyear_id], {}, 1)
        
        dict_1 = dict(data['form']['used_context'])
        dict_1['date_from'] = periods[0]['date_from']
        dict_1['date_to'] = periods[0]['date_to']
        
        dict1 = dict(data['form']['used_context'])
        dict1['date_from'] = periods[1]['date_from']
        dict1['date_to'] = periods[1]['date_to']
        
        dict2 = dict(data['form']['used_context'])
        dict2['date_from'] = periods[2]['date_from']
        dict2['date_to'] = periods[2]['date_to']
        
        dict3 = dict(data['form']['used_context'])
        dict3['date_from'] = periods[3]['date_from']
        dict3['date_to'] = periods[3]['date_to']
        
        dict4 = dict(data['form']['used_context'])
        dict4['date_from'] = periods[4]['date_from']
        dict4['date_to'] = periods[4]['date_to']
        
        dict5 = dict(data['form']['used_context'])            
        dict5['date_from'] = periods[5]['date_from']
        dict5['date_to'] = periods[5]['date_to']
        
        dict6 = dict(data['form']['used_context'])
        dict6['date_from'] = periods[6]['date_from']
        dict6['date_to'] = periods[6]['date_to']
        
        dict7 = dict(data['form']['used_context'])
        dict7['date_from'] = periods[7]['date_from']
        dict7['date_to'] = periods[7]['date_to']
        
        dict8 = dict(data['form']['used_context'])
        dict8['date_from'] = periods[8]['date_from']
        dict8['date_to'] = periods[8]['date_to']
        
        dict9 = dict(data['form']['used_context'])
        dict9['date_from'] = periods[9]['date_from']
        dict9['date_to'] = periods[9]['date_to']
        
        dict10 = dict(data['form']['used_context'])
        dict10['date_from'] = periods[10]['date_from']
        dict10['date_to'] = periods[10]['date_to']
        
        dict11 = dict(data['form']['used_context'])
        dict11['date_from'] = periods[11]['date_from']
        dict11['date_to'] = periods[11]['date_to']
        
        financial_report_obj = self.pool.get('account.financial.report')
        
        if data['form']['report_method'] == 'accrual':
            for report in financial_report_obj.browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
                
                re_balance1 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict_1)
                re_balance2 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict1)
                re_balance3 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict2)
                re_balance4 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict3)
                re_balance5 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict4)
                re_balance6 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict5)
                re_balance7 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict6)
                re_balance8 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict7)
                re_balance9 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict8)
                re_balance10 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict9)
                re_balance11 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict10)
                re_balance12 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict11)
                
                vals = {
                    'name': report.name,
                    'balance': report.balance * report.sign or 0.0,
                    'balance1': re_balance1.balance != 0 and re_balance1.balance * report.sign or re_balance1.balance,
                    'balance2': re_balance2.balance != 0 and re_balance2.balance * report.sign or re_balance2.balance,
                    'balance3': re_balance3.balance != 0 and re_balance3.balance * report.sign or re_balance3.balance,
                    'balance4': re_balance4.balance != 0 and re_balance4.balance * report.sign or re_balance4.balance,
                    'balance5': re_balance5.balance != 0 and re_balance5.balance * report.sign or re_balance5.balance,
                    'balance6': re_balance6.balance != 0 and re_balance6.balance * report.sign or re_balance6.balance,
                    'balance7': re_balance7.balance != 0 and re_balance7.balance * report.sign or re_balance7.balance,
                    'balance8': re_balance8.balance != 0 and re_balance8.balance * report.sign or re_balance8.balance,
                    'balance9': re_balance9.balance != 0 and re_balance9.balance * report.sign or re_balance9.balance,
                    'balance10': re_balance10.balance != 0 and re_balance10.balance * report.sign or re_balance10.balance,
                    'balance11': re_balance11.balance != 0 and re_balance11.balance * report.sign or re_balance11.balance,
                    'balance12': re_balance12.balance != 0 and re_balance12.balance * report.sign or re_balance12.balance,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                
                account_ids = []
                if report.display_detail == 'no_detail':                
                    lines2.append({
                                'name': 'Total %s'%report.name,
                                'balance': report.balance * report.sign or 0.0,
                                'type': 'report',
                                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                                'account_type': True, #used to underline the financial report balances
                            })
                    continue
                else:
                    lines.append(vals)
                if report.type == 'accounts' and report.account_ids:
                    account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
                elif report.type == 'account_type' and report.account_type_ids:
                    account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
                if not account_ids:
                    lines.remove(vals)
                else:
                    
                    child_lines = []
                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        
                        balance1 = account_obj.browse(self.cr, self.uid, account.id, context=dict_1)
                        balance2 = account_obj.browse(self.cr, self.uid, account.id, context=dict1)
                        balance3 = account_obj.browse(self.cr, self.uid, account.id, context=dict2)
                        balance4 = account_obj.browse(self.cr, self.uid, account.id, context=dict3)
                        balance5 = account_obj.browse(self.cr, self.uid, account.id, context=dict4)
                        balance6 = account_obj.browse(self.cr, self.uid, account.id, context=dict5)
                        balance7 = account_obj.browse(self.cr, self.uid, account.id, context=dict6)
                        balance8 = account_obj.browse(self.cr, self.uid, account.id, context=dict7)
                        balance9 = account_obj.browse(self.cr, self.uid, account.id, context=dict8)
                        balance10 = account_obj.browse(self.cr, self.uid, account.id, context=dict9)
                        balance11 = account_obj.browse(self.cr, self.uid, account.id, context=dict10)
                        balance12 = account_obj.browse(self.cr, self.uid, account.id, context=dict11)
                        
                        
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance != 0 and account.balance * report.sign or account.balance,
                            'balance1': balance1.balance != 0 and balance1.balance * report.sign or balance1.balance,
                            'balance2': balance2.balance != 0 and balance2.balance * report.sign or balance2.balance,
                            'balance3': balance3.balance != 0 and balance3.balance * report.sign or balance3.balance,
                            'balance4': balance4.balance != 0 and balance4.balance * report.sign or balance4.balance,
                            'balance5': balance5.balance != 0 and balance5.balance * report.sign or balance5.balance,
                            'balance6': balance6.balance != 0 and balance6.balance * report.sign or balance6.balance,
                            'balance7': balance7.balance != 0 and balance7.balance * report.sign or balance7.balance,
                            'balance8': balance8.balance != 0 and balance8.balance * report.sign or balance8.balance,
                            'balance9': balance9.balance != 0 and balance9.balance * report.sign or balance9.balance,
                            'balance10': balance10.balance != 0 and balance10.balance * report.sign or balance10.balance,
                            'balance11': balance11.balance != 0 and balance11.balance * report.sign or balance11.balance,
                            'balance12': balance12.balance != 0 and balance12.balance * report.sign or balance12.balance,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                        }
    
                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            child_lines.append(vals)
                    #insert line total into file report
                    total_line = {}
                    new_child_lines = []
                    for line in child_lines:
                        new_line =  dict(line)
                        new_child_lines.append(new_line)
                        if line.get('account_type', False) == 'view':
                            if line != child_lines[0]:
                                new_child_lines.append(total_line)
                            total_line = line
                            total_line['name'] = 'Total %s'%total_line['name']
                            total_line['account_type'] = True
                    new_child_lines.append(total_line)
                    lines += new_child_lines   
                    #------------------------------------------------------
                if lines:
                    lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance * report.sign or 0.0,
                        'balance1': re_balance1.balance != 0 and re_balance1.balance * report.sign or re_balance1.balance,
                        'balance2': re_balance2.balance != 0 and re_balance2.balance * report.sign or re_balance2.balance,
                        'balance3': re_balance3.balance != 0 and re_balance3.balance * report.sign or re_balance3.balance,
                        'balance4': re_balance4.balance != 0 and re_balance4.balance * report.sign or re_balance4.balance,
                        'balance5': re_balance5.balance != 0 and re_balance5.balance * report.sign or re_balance5.balance,
                        'balance6': re_balance6.balance != 0 and re_balance6.balance * report.sign or re_balance6.balance,
                        'balance7': re_balance7.balance != 0 and re_balance7.balance * report.sign or re_balance7.balance,
                        'balance8': re_balance8.balance != 0 and re_balance8.balance * report.sign or re_balance8.balance,
                        'balance9': re_balance9.balance != 0 and re_balance9.balance * report.sign or re_balance9.balance,
                        'balance10': re_balance10.balance != 0 and re_balance10.balance * report.sign or re_balance10.balance,
                        'balance11': re_balance11.balance != 0 and re_balance11.balance * report.sign or re_balance11.balance,
                        'balance12': re_balance12.balance != 0 and re_balance12.balance * report.sign or re_balance12.balance,
                        'type': 'report',
                        'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                        'account_type': True, #used to underline the financial report balances
                    })
                else:
                    income_lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance * report.sign or 0.0,
                        'balance1': re_balance1.balance != 0 and re_balance1.balance * report.sign or re_balance1.balance,
                        'balance2': re_balance2.balance != 0 and re_balance2.balance * report.sign or re_balance2.balance,
                        'balance3': re_balance3.balance != 0 and re_balance3.balance * report.sign or re_balance3.balance,
                        'balance4': re_balance4.balance != 0 and re_balance4.balance * report.sign or re_balance4.balance,
                        'balance5': re_balance5.balance != 0 and re_balance5.balance * report.sign or re_balance5.balance,
                        'balance6': re_balance6.balance != 0 and re_balance6.balance * report.sign or re_balance6.balance,
                        'balance7': re_balance7.balance != 0 and re_balance7.balance * report.sign or re_balance7.balance,
                        'balance8': re_balance8.balance != 0 and re_balance8.balance * report.sign or re_balance8.balance,
                        'balance9': re_balance9.balance != 0 and re_balance9.balance * report.sign or re_balance9.balance,
                        'balance10': re_balance10.balance != 0 and re_balance10.balance * report.sign or re_balance10.balance,
                        'balance11': re_balance11.balance != 0 and re_balance11.balance * report.sign or re_balance11.balance,
                        'balance12': re_balance12.balance != 0 and re_balance12.balance * report.sign or re_balance12.balance,
                        'type': 'report',
                        'level': 1,
                        'account_type': True, #used to underline the financial report balances
                    })
            from operator import itemgetter
            lines2 =  sorted(lines2, key=itemgetter('level'), reverse=True)
            lines += lines2
            lines += income_lines
        elif data['form']['report_method'] == 'cash':
            for report in financial_report_obj.browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
                
                re_balance1 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict_1)
                re_balance2 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict1)
                re_balance3 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict2)
                re_balance4 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict3)
                re_balance5 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict4)
                re_balance6 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict5)
                re_balance7 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict6)
                re_balance8 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict7)
                re_balance9 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict8)
                re_balance10 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict9)
                re_balance11 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict10)
                re_balance12 = financial_report_obj.browse(self.cr, self.uid, report.id, context=dict11)
                
                vals = {
                    'name': report.name,
                    'balance': report.balance_cash * report.sign or 0.0,
                    'balance1': re_balance1.balance_cash != 0 and re_balance1.balance_cash * report.sign or re_balance1.balance_cash,
                    'balance2': re_balance2.balance_cash != 0 and re_balance2.balance_cash * report.sign or re_balance2.balance_cash,
                    'balance3': re_balance3.balance_cash != 0 and re_balance3.balance_cash * report.sign or re_balance3.balance_cash,
                    'balance4': re_balance4.balance_cash != 0 and re_balance4.balance_cash * report.sign or re_balance4.balance_cash,
                    'balance5': re_balance5.balance_cash != 0 and re_balance5.balance_cash * report.sign or re_balance5.balance_cash,
                    'balance6': re_balance6.balance_cash != 0 and re_balance6.balance_cash * report.sign or re_balance6.balance_cash,
                    'balance7': re_balance7.balance_cash != 0 and re_bal.balance_cash_cashlance * report.sign or re_balance7.balance_cash,
                    'balance8': re_balance8.balance_cash != 0 and re_balance8.balance_cash * report.sign or re_balance8.balance_cash,
                    'balance9': re_balance9.balance_cash != 0 and re_balance9.balance_cash * report.sign or re_balance9.balance_cash,
                    'balance10': re_balance10.balance_cash != 0 and re_balance10.balance_cash * report.sign or re_balance10.balance_cash,
                    'balance11': re_balance11.balance_cash != 0 and re_balance11.balance_cash * report.sign or re_balance11.balance_cash,
                    'balance12': re_balance12.balance_cash != 0 and re_balance12.balance_cash * report.sign or re_balance12.balance_cash,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance_cash * report.sign or 0.0
                
                account_ids = []
                if report.display_detail == 'no_detail':                
                    lines2.append({
                                'name': 'Total %s'%report.name,
                                'balance': report.balance_cash * report.sign or 0.0,
                                'type': 'report',
                                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                                'account_type': True, #used to underline the financial report balances
                            })
                    continue
                else:
                    lines.append(vals)
                if report.type == 'accounts' and report.account_ids:
                    account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
                elif report.type == 'account_type' and report.account_type_ids:
                    account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
                if not account_ids:
                    lines.remove(vals)
                else:
                    
                    child_lines = []
                    for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        
                        balance1 = account_obj.browse(self.cr, self.uid, account.id, context=dict_1)
                        balance2 = account_obj.browse(self.cr, self.uid, account.id, context=dict1)
                        balance3 = account_obj.browse(self.cr, self.uid, account.id, context=dict2)
                        balance4 = account_obj.browse(self.cr, self.uid, account.id, context=dict3)
                        balance5 = account_obj.browse(self.cr, self.uid, account.id, context=dict4)
                        balance6 = account_obj.browse(self.cr, self.uid, account.id, context=dict5)
                        balance7 = account_obj.browse(self.cr, self.uid, account.id, context=dict6)
                        balance8 = account_obj.browse(self.cr, self.uid, account.id, context=dict7)
                        balance9 = account_obj.browse(self.cr, self.uid, account.id, context=dict8)
                        balance10 = account_obj.browse(self.cr, self.uid, account.id, context=dict9)
                        balance11 = account_obj.browse(self.cr, self.uid, account.id, context=dict10)
                        balance12 = account_obj.browse(self.cr, self.uid, account.id, context=dict11)
                        
                        if report.display_detail == 'detail_flat' and account.type == 'view':
                            continue
                        flag = False
                        
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance':  account.balance_cash != 0 and account.balance_cash * report.sign or account.balance_cash,
                            'balance1': balance1.balance_cash != 0 and balance1.balance_cash * report.sign or balance1.balance_cash,
                            'balance2': balance2.balance_cash != 0 and balance2.balance_cash * report.sign or balance2.balance_cash,
                            'balance3': balance3.balance_cash != 0 and balance3.balance_cash * report.sign or balance3.balance_cash,
                            'balance4': balance4.balance_cash != 0 and balance4.balance_cash * report.sign or balance4.balance_cash,
                            'balance5': balance5.balance_cash != 0 and balance5.balance_cash * report.sign or balance5.balance_cash,
                            'balance6': balance6.balance_cash != 0 and balance6.balance_cash * report.sign or balance6.balance_cash,
                            'balance7': balance7.balance_cash != 0 and balance7.balance_cash * report.sign or balance7.balance_cash,
                            'balance8': balance8.balance_cash != 0 and balance8.balance_cash * report.sign or balance8.balance_cash,
                            'balance9': balance9.balance_cash != 0 and balance9.balance_cash * report.sign or balance9.balance_cash,
                            'balance10': balance10.balance_cash != 0 and balance10.balance_cash * report.sign or balance10.balance_cash,
                            'balance11': balance11.balance_cash != 0 and balance11.balance_cash * report.sign or balance11.balance_cash,
                            'balance12': balance12.balance_cash != 0 and balance12.balance_cash * report.sign or balance12.balance_cash,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                            'account_type': account.type,
                        }
    
                        if data['form']['debit_credit']:
                            vals['debit'] = account.debit
                            vals['credit'] = account.credit
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                            flag = True
                        if data['form']['enable_filter']:
                            vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance_cash * report.sign or 0.0
                            if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                                flag = True
                        if flag:
                            child_lines.append(vals)
                    #insert line total into file report
                    total_line = {}
                    new_child_lines = []
                    for line in child_lines:
                        new_line =  dict(line)
                        new_child_lines.append(new_line)
                        if line.get('account_type', False) == 'view':
                            if line != child_lines[0]:
                                new_child_lines.append(total_line)
                            total_line = line
                            total_line['name'] = 'Total %s'%total_line['name']
                            total_line['account_type'] = True
                    new_child_lines.append(total_line)
                    lines += new_child_lines   
                    #------------------------------------------------------
                if lines:
                    lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance_cash * report.sign or 0.0,
                        'balance1': re_balance1.balance_cash != 0 and re_balance1.balance_cash * report.sign or re_balance1.balance_cash,
                        'balance2': re_balance2.balance_cash != 0 and re_balance2.balance_cash * report.sign or re_balance2.balance_cash,
                        'balance3': re_balance3.balance_cash != 0 and re_balance3.balance_cash * report.sign or re_balance3.balance_cash,
                        'balance4': re_balance4.balance_cash != 0 and re_balance4.balance_cash * report.sign or re_balance4.balance_cash,
                        'balance5': re_balance5.balance_cash != 0 and re_balance5.balance_cash * report.sign or re_balance5.balance_cash,
                        'balance6': re_balance6.balance_cash != 0 and re_balance6.balance_cash * report.sign or re_balance6.balance_cash,
                        'balance7': re_balance7.balance_cash != 0 and re_bal.balance_cash_cashlance * report.sign or re_balance7.balance_cash,
                        'balance8': re_balance8.balance_cash != 0 and re_balance8.balance_cash * report.sign or re_balance8.balance_cash,
                        'balance9': re_balance9.balance_cash != 0 and re_balance9.balance_cash * report.sign or re_balance9.balance_cash,
                        'balance10': re_balance10.balance_cash != 0 and re_balance10.balance_cash * report.sign or re_balance10.balance_cash,
                        'balance11': re_balance11.balance_cash != 0 and re_balance11.balance_cash * report.sign or re_balance11.balance_cash,
                        'balance12': re_balance12.balance_cash != 0 and re_balance12.balance_cash * report.sign or re_balance12.balance_cash,
                        'type': 'report',
                        'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                        'account_type': True, #used to underline the financial report balances
                    })
                else:
                    income_lines.append({
                        'name': 'Total %s'%report.name,
                        'balance': report.balance_cash * report.sign or 0.0,
                        'balance1': re_balance1.balance_cash != 0 and re_balance1.balance_cash * report.sign or re_balance1.balance_cash,
                        'balance2': re_balance2.balance_cash != 0 and re_balance2.balance_cash * report.sign or re_balance2.balance_cash,
                        'balance3': re_balance3.balance_cash != 0 and re_balance3.balance_cash * report.sign or re_balance3.balance_cash,
                        'balance4': re_balance4.balance_cash != 0 and re_balance4.balance_cash * report.sign or re_balance4.balance_cash,
                        'balance5': re_balance5.balance_cash != 0 and re_balance5.balance_cash * report.sign or re_balance5.balance_cash,
                        'balance6': re_balance6.balance_cash != 0 and re_balance6.balance_cash * report.sign or re_balance6.balance_cash,
                        'balance7': re_balance7.balance_cash != 0 and re_bal.balance_cash_cashlance * report.sign or re_balance7.balance_cash,
                        'balance8': re_balance8.balance_cash != 0 and re_balance8.balance_cash * report.sign or re_balance8.balance_cash,
                        'balance9': re_balance9.balance_cash != 0 and re_balance9.balance_cash * report.sign or re_balance9.balance_cash,
                        'balance10': re_balance10.balance_cash != 0 and re_balance10.balance_cash * report.sign or re_balance10.balance_cash,
                        'balance11': re_balance11.balance_cash != 0 and re_balance11.balance_cash * report.sign or re_balance11.balance_cash,
                        'balance12': re_balance12.balance_cash != 0 and re_balance12.balance_cash * report.sign or re_balance12.balance_cash,
                        'type': 'report',
                        'level': 1,
                        'account_type': True, #used to underline the financial report balances
                    })
            from operator import itemgetter
            lines2 =  sorted(lines2, key=itemgetter('level'), reverse=True)
            lines += lines2
            lines += income_lines
        data = lines
        if {} in lines:
            data = []
            for l in lines:
                if l: data.append(l)
        
        return data


from openerp.netsvc import Service
del Service._services['report.account.financial.report']

report_sxw.report_sxw('report.account.financial.report', 'account.financial.report',
    'addons/init_barry_report_financial/report/account_financial_report.rml', parser=report_account_common_inherit)

report_sxw.report_sxw('report.income.account.financial.report', 'account.financial.report',
    'init_barry_report_financial/report/incoming_account_financial_report.rml', parser=report_account_common_inherit)

report_sxw.report_sxw('report.income.account.financial.month.report', 'account.financial.report',
    'init_barry_report_financial/report/incoming_account_financial_month_report.rml', parser=report_account_common_inherit)

report_sxw.report_sxw('report.income.account.financial.year.report', 'account.financial.report',
    'init_barry_report_financial/report/incoming_account_financial_year_report.rml', parser=report_account_common_inherit)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
