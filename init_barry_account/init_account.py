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
import openerp.addons.decimal_precision as dp

class account_account(osv.osv):
    _inherit = "account.account"
    _columns = {
        
    }
    
account_account()
