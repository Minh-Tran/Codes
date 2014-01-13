# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv

class accounting_report(osv.osv_memory):
    _inherit = "accounting.report"
    _columns = {
            'report_method': fields.selection([('cash', 'Cash method'),
                                         ('accrual', 'Accrual method'),
                                        ], 'Report method', required=True),
            'interval': fields.selection([('month', 'Month'),
                                         ('quater', 'Quater'),
                                         ('year', 'Year'),
                                        ], 'Interval'),

              }
    _defaults = {
            'report_method': 'accrual',
            'interval': 'month',
    }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        
        
        data['form'].update(self.read(cr, uid, ids, ['interval','date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter'], context=context)[0])
        
        if context.get('incoming_report', False):
            if data['form']['interval'] == 'quater':
                return {
                'type': 'ir.actions.report.xml',
                'report_name': 'income.account.financial.report',
                'datas': data,
                }
            elif data['form']['interval'] == 'month':
                return {
                'type': 'ir.actions.report.xml',
                'report_name': 'income.account.financial.month.report',
                'datas': data,
                }
            else:
                return {
                'type': 'ir.actions.report.xml',
                'report_name': 'income.account.financial.year.report',
                'datas': data,
                }
            
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.financial.report',
            'datas': data,
        }
    
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from',  'date_to',  'fiscalyear_id', 'journal_ids', 'period_from', 'period_to',  'filter',  'chart_account_id', 'target_move', 'report_method', 'interval'], context=context)[0]
        for field in ['fiscalyear_id', 'chart_account_id', 'period_from', 'period_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = dict(used_context, lang=context.get('lang', 'en_US'))
        return self._print_report(cr, uid, ids, data, context=context)
    

accounting_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
