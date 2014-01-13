# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "INIT Print Invoice",
        "version" : "1.0",
        "author" : "Init Tech",
        "website" : "http://www.init.vn",
        "category" : "INIT Modules",
        "description" : """Print Invoice Barry""",
        "depends" : ["base","account","report_aeroo"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : ['invoice_report.xml',
                        'invoice_view.xml',
                        'wizard/wizard_send_multi_invoice_view.xml'
                        ],
        'installable': True,
        'auto_install': False,
        'application': True,
}
