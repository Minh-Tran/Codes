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

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp



class account_account(osv.osv):

    _inherit = "account.account"
    
    def __compute_cash(self, cr, uid, ids, field_names, arg=None, context=None,
                  query='', query_params=()):
        
        mapping = {
            'balance_cash': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance_cash",
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END FROM account_account WHERE id IN (l.account_id)) as foreign_balance",
        }
        #get all the necessary accounts
        children_and_consolidated = self._get_children_and_consol(cr, uid, ids, context=context)
        #compute for each account the balance/debit/credit from the move lines
        accounts = {}
        res = {}
        null_result = dict((fn, 0.0) for fn in field_names)
        if children_and_consolidated:
            aml_query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)

            wheres = [""]
            if query.strip():
                wheres.append(query.strip())
            if aml_query.strip():
                wheres.append(aml_query.strip())
            filters = " AND ".join(wheres)
            # IN might not work ideally in case there are too many
            # children_and_consolidated, in that case join on a
            # values() e.g.:
            # SELECT l.account_id as id FROM account_move_line l
            # INNER JOIN (VALUES (id1), (id2), (id3), ...) AS tmp (id)
            # ON l.account_id = tmp.id
            # or make _get_children_and_consol return a query and join on that
            
            request = ("SELECT distinct(l.id) as id " \
                       " FROM account_move_line l" \
                       " inner join account_invoice inv on inv.move_id = l.move_id" \
                       " inner join account_account acc on l.account_id = acc.id" \
                       " WHERE l.account_id IN %s " \
                            + filters)
            params = (tuple(children_and_consolidated),) + query_params
            
            cr.execute(request, params)
            move_inv_ids = []
            for row in cr.dictfetchall():
                move_inv_ids += [row['id']]
                
            request = ("SELECT distinct(inv.id, l.account_id) as ids,inv.id, l.account_id  " \
                       " FROM account_move_line l" \
                       " inner join account_invoice inv on inv.move_id = l.move_id" \
                       " WHERE l.account_id IN %s " \
                            + filters +
                       " GROUP BY inv.id,l.account_id")
            
            params = (tuple(children_and_consolidated),) + query_params            
            cr.execute(request, params)
            
            inv_ids = {'id': [], 'data': {}}
            for row in cr.dictfetchall():
                if row['id'] not in inv_ids['id']:
                    inv_ids['id'] += [row['id']]
                if not row['id'] in inv_ids['data'].keys():
                    inv_ids['data'].update({row['id']: [row['account_id']]})
                else:
                    inv_ids['data'][row['id']] += [row['account_id']]
            
            request = ("SELECT l.account_id as id, " +\
                       ', '.join(mapping.values()) +
                       " FROM account_move_line l" \
                       " WHERE l.id NOT IN " \
                            + str(tuple(move_inv_ids+[-1,-1])) +
                       " AND l.account_id IN %s " \
                            + str(filters) +
                       " GROUP BY l.account_id")
            params = (tuple(children_and_consolidated),) + query_params
           
            cr.execute(request, params)

            for row in cr.dictfetchall():
                accounts[row['id']] = row
            
            account_invoice_obj = self.pool.get('account.invoice')
            for obj in account_invoice_obj.browse(cr, uid, inv_ids['id']):
                total = 0.0
                for pay in obj.payment_ids:
                    total += pay.debit - pay.credit
                total = total * 2  
                if not total:
                    continue  
                for account_id in inv_ids['data'][obj.id]:                   
                    if accounts and account_id in accounts.keys() and 'balance_cash' in accounts[account_id].keys():
                        for ml in obj.move_id.line_id:
                            print ml.account_id.id, abs(-ml.debit + ml.credit)
                            if ml.account_id.id == account_id and abs(-ml.debit + ml.credit) <= abs(total):
                                accounts[account_id]['balance_cash'] += ml.debit - ml.credit
                                total -= ml.debit - ml.credit
                    else:
                        for ml in obj.move_id.line_id:
                            if ml.account_id.id == account_id  and abs(-ml.debit + ml.credit) <= abs(total):
                                if account_id not in accounts.keys():
                                    accounts.update({account_id: {'balance_cash': ml.debit - ml.credit}})
                                else:
                                    accounts[account_id].update({'balance_cash': ml.debit - ml.credit})
                                total -= ml.debit - ml.credit
            print accounts,'aaa'
            # consolidate accounts with direct children
            children_and_consolidated.reverse()
            brs = list(self.browse(cr, uid, children_and_consolidated, context=context))
            sums = {}
            currency_obj = self.pool.get('res.currency')
            while brs:
                current = brs.pop(0)
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    
                    for child in current.child_id:
                        if child.company_id.currency_id.id == current.company_id.currency_id.id:
                            sums[current.id][fn] += sums[child.id][fn]
                        else:
                            sums[current.id][fn] += currency_obj.compute(cr, uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)

                # as we have to relay on values computed before this is calculated separately than previous fields
                if current.currency_id and current.exchange_rate and \
                            ('adjusted_balance' in field_names or 'unrealized_gain_loss' in field_names):
                    # Computing Adjusted Balance and Unrealized Gains and losses
                    # Adjusted Balance = Foreign Balance / Exchange Rate
                    # Unrealized Gains and losses = Adjusted Balance - Balance
                    adj_bal = sums[current.id].get('foreign_balance', 0.0) / current.exchange_rate
                    sums[current.id].update({'adjusted_balance': adj_bal, 'unrealized_gain_loss': adj_bal - sums[current.id].get('balance', 0.0)})

            for id in ids:
                res[id] = sums.get(id, null_result)
        else:
            for id in ids:
                res[id] = null_result
        
        return res

    _columns = {
        'balance_cash': fields.function(__compute_cash, digits_compute=dp.get_precision('Account'), string='Cash Basic', multi='balance_cash'),
    }

account_account()

