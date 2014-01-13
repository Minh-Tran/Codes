# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "INIT Financial Report",
        "version" : "1.0",
        "author" : "Init Tech",
        "website" : "http://www.init.vn",
        "category" : "INIT Modules",
        "description" : """Print Balance Sheet and Income Statement""",
        "depends" : ["base","account"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        'account_financial_report.xml',
                        'wizard/account_common_report.xml',
                        ],
        'installable': True,
        'auto_install': False,
        'application': True,
}
