# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "INIT Check",
        "version" : "1.0",
        "author" : "Init Tech",
        "website" : "http://www.init.vn",
        "category" : "INIT Modules",
        "description" : """Create check for multi invoice same supplier""",
        "depends" : ["base","account"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        'wizard/wizard_create_check_view.xml',
                        'account_voucher_view.xml',
                        ],
        'installable': True,
        'auto_install': False,
        'application': True,
}
