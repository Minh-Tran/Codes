from openerp.osv import fields, osv

class account_financial_report(osv.osv_memory):
    _inherit = "account.financial.report"
    
    def _get_balance(self, cr, uid, ids, field_names, args, context=None):
        account_obj = self.pool.get('account.account')
        res = {}
        for report in self.browse(cr, uid, ids, context=context):
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in field_names)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                for a in report.account_ids:
                    for field in field_names:
                        res[report.id][field] += getattr(a, field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                report_types = [x.id for x in report.account_type_ids]
                account_ids = account_obj.search(cr, uid, [('user_type','in', report_types), ('type','!=','view')], context=context)
                for a in account_obj.browse(cr, uid, account_ids, context=context):
                    for field in field_names:
                        res[report.id][field] += getattr(a, field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._get_balance(cr, uid, [report.account_report_id.id], field_names, False, context=context)
                for key, value in res2.items():
                    for field in field_names:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._get_balance(cr, uid, [rec.id for rec in report.children_ids], field_names, False, context=context)
                for key, value in res2.items():
                    for field in field_names:
                        res[report.id][field] += value[field]
        return res
    
    _columns = {
              'balance_cash': fields.function(_get_balance, 'Balance', multi='balance'),}