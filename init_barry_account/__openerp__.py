# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "INIT Barry Account",
        "version" : "1.0",
        "author" : "Init Tech",
        "website" : "http://www.init.vn",
        "category" : "INIT Modules",
        "description" : """ Requirement Account""",
        "depends" : ["base","account"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        "security/account_security.xml",
                        "init_account_view.xml",
                        "supplier_invoice_view.xml",
                         ],
        'installable': True,
        'auto_install': False,
        'application': True,
}
