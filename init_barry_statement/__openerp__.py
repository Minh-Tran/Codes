# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "INIT Print Statement",
        "version" : "1.0",
        "author" : "Init Tech",
        "website" : "http://www.init.vn",
        "category" : "INIT Modules",
        "description" : """Print Statement Barry""",
        "depends" : ["base","account"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : ['statement_report.xml',
                        'statement_view.xml',
                        ],
        'installable': True,
        'auto_install': False,
        'application': True,
}
