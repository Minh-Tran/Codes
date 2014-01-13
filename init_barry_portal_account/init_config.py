

from mx import DateTime
from xmllib import _Name
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from tools import config
from osv import fields, osv
from dateutil.relativedelta import relativedelta
from tools.translate import _
from datetime import date, datetime, timedelta
import calendar
import datetime
import string
import netsvc
import decimal_precision as dp

class account_invoice(osv.osv):     
    
    _inherit = "account.invoice"
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        
        new_args = []
        new_args.extend(args)
        for arg in args:
#            print arg,type(arg), len(arg) == 3 and arg[0], len(arg) == 3 and  arg[2]
            if len(arg) == 3 and arg[0] == 'partner_id' and type(arg[2]) in (type(' '), type({})) and 'user_id' in arg[2]:
                dic = arg[2]
                user_obj = self.pool.get('res.users').browse(cr, uid, dic['user_id'])
                new_args.remove(arg)
                if user_obj.partner_id:
                    new_args.append(['partner_id', '=', user_obj.partner_id.id])
        
        return super(account_invoice, self).search(cr, uid, new_args, offset, limit,
                order, context=context, count=count)
account_invoice()

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'payment_url': fields.char('Payment URL', 255),
    }
    
    def open_payment_url(self, cr, uid):
        payment_url = self.pool.get('res.users').browse(cr, uid, uid).company_id.payment_url
        if payment_url:
            return {
                    'type': 'ir.actions.act_url',
                    'url':payment_url,
                    'target': 'current'
                    }
        return True
    
res_company()
