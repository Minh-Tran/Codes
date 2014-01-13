import time
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler

class statement(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(statement, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                                  'get_date': self.get_date,
                                  'get_memo': self.get_memo,
                                  'get_increase': self.get_increase,
                                  'get_decrease': self.get_decrease,
                                  'get_balance_due': self.get_balance_due,
                                  'get_previous_balance': self.get_previous_balance
                                  })
    def get_date(self, move_ids):
        dt = move_ids.date
        return dt
    def get_memo(self, move_ids):
        memo = move_ids.name
        return memo
    def get_increase(self, move_ids):
        if move_ids.credit:
            cr = move_ids.credit
        str = move_ids.company_id.currency_id.symbol + repr(cr)
        str.encode('utf8')
        return str
    def get_decrease(self, move_ids):
        if move_ids.debit:
            db = move_ids.debit
        str = move_ids.company_id.currency_id.symbol + repr(db)
        str.encode('utf8')
        return str
    def get_balance_due(self, payment):
        location_obj = pooler.get_pool(self.cr.dbname).get('account.voucher.line')
        if payment.line_ids:
            ids = payment.line_ids.id
            amount_original = location_obj.read(self.cr, self.uid, ids[0])
            result = amount_original['amount_original']-amount_original['amount']
        else:
            result =  0.0
        str = payment.currency_id.symbol + repr(result)
        str.encode('utf8')
        return str
    def get_previous_balance(self, payment):
        location_obj = pooler.get_pool(self.cr.dbname).get('account.voucher.line')
        if payment.line_ids:
            ids = payment.line_ids.id
            amount_original = location_obj.read(self.cr, self.uid, ids[0])
            result = amount_original['amount_original']
        else:
            result =  0.0    
        str = payment.currency_id.symbol + repr(result)
        str.encode('utf8')
        return str
        #balance = voucher_lines.amount_unreconciled - voucher_lines.amount
        #return balance
report_sxw.report_sxw('report.statement','account.voucher','addons/init_barry_statement/report/statement.rml',parser=statement)